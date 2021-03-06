from __future__ import unicode_literals
from . import admin
from flask import request,url_for,redirect,jsonify,make_response,render_template,session
from  ...mod_util import create_hashid
from ..utils import requires_roles
#from flask_login import login_required
from ..utils import requires_roles

from wtforms import PasswordField,TextField,Form
from flask_wtf import FlaskForm
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.contrib.sqla.validators import Unique
from wtforms.validators import InputRequired,EqualTo,Email
from flask_admin.form import SecureForm
from flask_login import current_user
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView,expose,AdminIndexView
from ... import db,charts
from ...models.users import (User,Questions,Roles,
Stream,Organization,Subject,Submissions,Semester,Electives,semesterelective)
from werkzeug.security import generate_password_hash

from .forms import SubmissionForm,StreamForm
from flask_googlecharts import PieChart
import pdfkit
#BaseView is not for models it is for a standalone-view
# ModelView is for Models
#AdminIndexView is for Admin Home page

#try using ajax for loading fields
class MyPassField(PasswordField):
    def process_data(self, value):
        self.data = ''  # even if password is already set, don't show hash here
        # or else it will be double-hashed on save
        self.orig_hash = value

    def process_fromdata(self, valuelist):
        value = ''
        if valuelist:
            value = valuelist[0]
        if value:
            self.data = generate_password_hash(
            value,method='pbkdf2:sha512',salt_length=64)
        else:
            self.data = self.orig_hash
    def __init__(self,name, **kwargs):
       # You can pass name and other parameters if you want to
       super(MyPassField, self).__init__(name,**kwargs)


class MyBaseForm(SecureForm):
    #used for stripping whitespace
    class Meta:
        def bind_field(self, form, unbound_field, options):
            filters = unbound_field.kwargs.get('filters', [])
            if my_strip_filter not in filters:
                filters.append(my_strip_filter)
            return unbound_field.bind(form=form, filters=filters, **options)

def my_strip_filter(value):
    if value is not None and hasattr(value, 'strip'):
        return value.strip()
    return value

class CustomModelView(ModelView):
    def is_accessible(self):
          return current_user.is_authenticated and current_user.is_admin()
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login',next=request.url))
    # IF you enable CsrfProtect switch to wtforms Form class instead of secure form
    form_base_class=MyBaseForm
    # form_base_class=Form
    # form_base_class=FlaskForm




class UserView(CustomModelView):

    column_searchable_list = ( User.fname,User.lname)
    column_exclude_list=['password_hash',]
    form_excluded_columns=('user_sub',)
    form_columns=('fname','lname','password',
    'confirm_password','email','created_on',
    'confirmed','organizationid','role')
    column_editable_list = ('fname','lname','email','role')

    column_labels=dict(fname='First Name',
    lname='Last Name',password_hash='Password',
    organizationid='Organization',
    )

    form_overrides=dict(password=MyPassField)



    form_extra_fields={
    'password':MyPassField('Password',validators=[InputRequired(),EqualTo('confirm_password',
    message='Passwords must match ')]),
    'confirm_password':PasswordField('Confirm password',validators=[InputRequired()])
    }

    form_args=dict(password=dict(
    validators=[InputRequired(),EqualTo('confirm_password',
    message='Passwords must match ')]),

    confirm_password=dict(validators=[InputRequired()]),
    created_on=dict(render_kw={'disabled':'disabled'}),
    email=dict(validators=[Unique(model=User, db_session=db.session,column='email'),Email(message='Enter a valid email')]),
    lname=dict(validators=[Unique(model=User,db_session=db.session,column='lname')])
    )


admin.add_view(UserView(User,db.session))
# admin.add_view(UserView(name='hello'))

class QuestionView(CustomModelView):

    column_exclude_list=['question_sub',]
    form_excluded_columns=['question_sub']
    column_labels=dict(question='Question',
    organization_question_id='Organization ID')

    form_args = {
        # 'org_ques_id':
        'organization_question_id': {
            #add a current user proxy right here
            'query_factory': lambda: db.session.query(Organization).filter_by(id = current_user.organization_id)
        }
    }

admin.add_view(QuestionView(Questions,db.session))

class StreamView(CustomModelView):
    form_columns=['stream',]
    form_excluded_columns=['submissions_id']

admin.add_view(StreamView(Stream,db.session))
class SubjectView(CustomModelView):
    #RECHECK HERE
    column_editable_list = ('subject_name',)
    column_searchable_list = ( Subject.subject_name,Stream.stream,Semester.semester_name)
    column_exclude_list=['submission_rel']
    column_display_all_relations=True

    column_filters = (Subject.stream,Semester.semester_name)
    form_excluded_columns=['submission_rel']
    column_labels=dict(streamsub='Stream',subject_ref="Semester",teacher_id="Teacher")

    # column_list=dict(stream='stream',semester='semester',teacher_name='teacher_name',subject_name='Subject')

    #form_columns=['stream','subjects',]
    #form_excluded_columns=['sub_id']
admin.add_view(SubjectView(Subject,db.session))

class SemesterView(CustomModelView):
    form_excluded_columns=["subject_col"]
    column_labels=dict(semester_name='Semester',)
admin.add_view(SemesterView(Semester,db.session))

class ElectivesView(CustomModelView):
    # column_hide_backrefs = True
    column_labels=dict(subject_relationship='Subjects',semester_id='Semester',stream_elect='Stream')
    column_list=['elective_name','subject_relationship','semester_id','stream_elect']
    form_columns=['elective_name','semester_id','stream_elect']
    # column_display_all_relations=True


admin.add_view(ElectivesView(Electives,db.session))
class LinkView(BaseView):
    @expose('/',methods=['GET','POST'])
    @requires_roles('admin')
    def index(self):
        #formdata=[(stream.id,stream.stream) for stream in Stream.query.all()]
        form=StreamForm()
        form.elective_data.choices=[(0,"Select an Elective")]

        #form=StreamForm(stream=formdata)
        return self.render('admin/link.html',form=form)

    @expose('/_generatelink',methods=['GET'])
    @requires_roles('admin')
    def genlink(self):
        if request.method == "GET":

            stream_name=request.args.get('b',0,type=int)
            semester_name=request.args.get('a',0,type=int)
            # print(semester_name)
            # elective_name=[(elective.elective_name_id,elective.elective)
            # for elective in Subject.query.filter_by(semester=semester_name,stream=stream_name).join(Stream)]
            elective_name=[(elective.id,elective.elective_name)
            for elective in Electives.query.filter(Electives.semester_id.any(id=semester_name),Electives.stream==stream_name)] or None

            # print(elective_name)
            # print(stream_name)

            # print(request.referrer)
            url=url_for('question.question_red',hashid=create_hashid(stream_name),
            semester=create_hashid(semester_name))


            # print(url)


        return jsonify(d=url,elective=elective_name)
        # return jsonify(d=url)
    # @expose('/_generatelink',methods=['GET'])
    # @requires_roles('admin')
    # def elective(self):
    #     pass


    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login',next=request.url))




admin.add_view(LinkView(name='Generate Link',endpoint='linkgen'))

class  SubmissionView(CustomModelView):
    column_sortable_list = ('date',)
    column_searchable_list=(Subject.subject_name,)


admin.add_view(SubmissionView(Submissions,db.session))

class ResultsView(BaseView):
    @expose('/',methods=["GET","POST"])
    @requires_roles('admin')
    def index(self):

        # my_chart=PieChart("new_chart",options={'title': 'My Chart', "width": 500,"height": 300,"is3D":True})
        # ans_yes=Submissions.query.filter_by(submission=1,question_id=1,user_id=2).count()
        # ans_no=Submissions.query.filter_by(submission=2,question_id=1,user_id=2).count()
        # print("\t\t\tANS_YES",ans_yes)
        # print("\t\t\tANS_No",ans_no)
        # my_chart.add_column("string", "Answer")
        # my_chart.add_column("number", "percent")
        # my_chart.add_rows([["Yes", ans_yes],
        #                 ["NO", ans_no],
        #                 ])
        # charts.register(my_chart)
        form=SubmissionForm()

        form.subject_select.choices=[(0,"Select a Subject")]
        form.teacher_select.choices=[(0,"Select a Teacher")]
        question=[(ques.id,ques.question) for ques in Questions.query.all()]

        return self.render('admin/results.html',form=form,question=question)
    @expose('/_submissions',methods=["GET"])
    @requires_roles('admin')
    def submissions(self):
        if request.method=="GET":
            try:
                stream_id=request.args.get('b',0,type=int)
                semester_id=request.args.get('c',0,type=int)



                data=[(dat.id,dat.subject_name) for dat in Subject.query.filter_by(stream=stream_id,semester=semester_id)]
                # print(data)
                return jsonify(data)
                # if len(subject_id) > 0:
                #     # data=[(dat.id,dat.subject_name) for dat in Subject.query.filter_by(stream=stream_id)]
                #     data=[(row.id,row.fname)  for row in  User.query.filter(User.subject_det.any(id=subject_id)).all()]
                #     print(data)
                #     return jsonify(data)

            except Exception as e:
                return jsonify(success=0, error_msg=str(e))


    @expose('/_charts',methods=["GET","POST"])
    @requires_roles('admin')
    def load_chart(self):
        stream_id=request.args.get('stream',0,type=int)
        subject_id=request.args.get('subject',0,type=int)
        teacher_id=request.args.get('teacher',0,type=int)
        question=[(ques.id,ques.question) for ques in Questions.query.all()]
        chart_data=[]
        dictv =request.form.to_dict()
        dictv.pop('csrf_token')

        # print(dictv)
        suggestions=[a.suggestions for a in Submissions.query.filter_by(subject_id=dictv['subject_select'],
        user_id=dictv['teacher_select'],
        stream_id=dictv['stream']).all() if str(a.suggestions) not in 'None' ]

        # print(suggestions)
        try:

            for key,value in question:
                ans_yes=Submissions.query.filter_by(submission=1,question_id=key,
                subject_id=dictv['subject_select'],user_id=dictv['teacher_select'],stream_id=dictv['stream']).count()

                ans_no=Submissions.query.filter_by(submission=2,question_id=key,
                subject_id=dictv['subject_select'],user_id=dictv['teacher_select'],stream_id=dictv['stream']).count()

                ans_no_comment=Submissions.query.filter_by(submission=3,question_id=key,
                subject_id=dictv['subject_select'],user_id=dictv['teacher_select'],stream_id=dictv['stream']).count()

                my_chart=PieChart(("teacher_chart{0}").format(key),
                options={'title': 'Submission', "width": 500,"height": 300,
                "is3D":'True',"pieSliceText":'percentage',
                'tooltip' : {'trigger': 'none'},'chartArea': {  'width': "100%", 'height': "50%" },
                'legend':{'position':'labeled'}
                }
                )
                # 'legend': { 'position': 'labeled','labeledValueText': 'both',
                # 'textStyle': {'fontName': 'Roboto','fontSize': 13,'color':'blue'}
                # }
                my_chart.add_column("string", "Answer")
                my_chart.add_column("number", "percent")

                my_chart.add_rows([["({0}) Yes".format(ans_yes), ans_yes],["({0}) No".format(ans_no), ans_no],["({0}) No Comment ".format(ans_no_comment), ans_no_comment]])
                chart_data.append((my_chart.name,key,value))
                charts.register(my_chart)


            return self.render('admin/result_chart.html',chart_data=chart_data,suggestions=suggestions),200
        except  Exception as e:
            print(e)
            return jsonify(message='Empty data'),200

    @expose('/_pdfgen',methods=["GET","POST"])
    def pdfgen(self):

        # from flask import Response,send_file
        #
        # dictv =request.form.to_dict()
        # dictv=request.form['sendD'];
        print('gekk')
        dictv=request.form.to_dict();
        dic=request.form['sendD']
        # print('{0}'.format(dictv['sendD']))
        # print(dic)
        # print(dictv)
        options={'page-size': 'A4',

    'encoding': "UTF-8",

    }
    #merge changes from production pc ***************************^
    # 'margin-top': '0.70in',
    # 'margin-right': '0.70in',
    # 'margin-bottom': '.60in',
    # 'margin-left': '0.60in',
        # options={'page-size': 'A4',


        # 'encoding': "UTF-8"}
    #Windows

        import platform
        if platform.system() =="Windows":
            css=r'main.css' # Absolute path required on Windows.
            path_to_wk=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            config = pdfkit.configuration(wkhtmltopdf=path_to_wk)
            pdfk=pdfkit.from_string(dictv['sendD'],False,options=options,configuration=config,css=css)
    #linux
        else:
            css=['FMSapp/Modules/Admin/main.css']
            import html
            pdfk=pdfkit.from_string(dictv['sendD'],False,options=options,css=css)

            # pdfk=pdfkit.from_string(dictv['sendD'],False,css=css)
        # pdfk=pdfkit.from_string(dictv,False)
        # # #

        response = make_response(pdfk, 200)
        # response.headers['Content-type'] = 'application/octet-stream'
        # response.headers['Content-type'] = "application/pdf;filename=outpu.pdf"
        # response.headers['Content-type'] = "blob"
        response.headers['Content-disposition'] = "attachment;filename={0}.pdf".format(dictv['tdata'].replace("'","\'"))
        # reponse.headers['Set-Cookie']="fileDownload=true; path=/"
        # reponse.set_cookie('Set-Cookie',"fileDownload=true; path=/")

        return response
        # return 'success'
        # response.headers['Set-Cookie'] = ''

        #
        # return redirect(url_for('viewhome.home'))
        #
        # chart_data=session['chart']
        # print(chart_data)
        # self.render('admin/result_chart.html',chart_data=chart_data)

    @expose('/_sem_dw',methods=["GET"])
    def sem_dw():
        data=request.form.to_dict()

    # @expose('/_download_all',methods=["GET"])
    # def dw_all(self):
    #
    #
    #     # chart_d=self.render()
    #     # users=[a.fname.strip() for a in User.query.filter_by(role='teacher').all()]
    #
    #     # users=[user.fname.strip() for user in db.session.query(User).filter_by(role_id=2).all()]
    #     # subjects=[(user.)_name for subject in db.session.query(Subject).all()]
    #     # questions=[question.question for question in db.session.query(Questions).filter_by().all()]
    #
    #     # users=User.query.filter(Roles.role_name=='teacher').all()
    #     # print(users,subjects,questions)
    #     # from flask import render_template
    #     # pdf=render_template('admin/test_chart.html')
    #     # pdfkit.from_string(pdf,False,options=options)
    #     # response = make_response(pdf, 200)
    #     # response.headers['Content-type'] = "application/pdf;filename=outpu.pdf"
    #     # response.headers['Content-disposition'] = "inline"
    #     question=[(ques.id,ques.question) for  ques in Questions.query.all()]
    #
    #     teacher_details=[(teacher.user_id,teacher.submission_r,teacher.stsub,teacher.usersub) \
    #     for teacher in Submissions.query.order_by(Submissions.date.desc()).limit(30).all()]
    #
    #     teacher_role=[(teacher.fname,teacher.role)for teacher in User.query.join(Roles).filter(Roles.role_name=='teacher')]
    #     teacher_sub=[(teacher.id,teacher.teacher,teacher.teacher_id) for teacher in Subject.query.join(User).filter(Subject.id==Submissions.subject_id)]
    #     print(teacher_sub)
    #
    #     print(teacher_role)
    #     chart_data=[]
    #     # for  name in teacher_details:
    #     #     print(name[3])
    #     #     for no,ques in question:
    #     #         ans=Submissions.query.filter_by(submission=1,user_id=name[0],question_id=no).count()
    #     #         ans1=Submissions.query.filter_by(submission=2,user_id=name[0],question_id=no).count()
    #     #
    #     #         print(no,"",ques,"\n",'yes'," ",ans," no",ans1)
    #     #         print('-'*25)
    #     #     print('+'*30)
    #
    #
    #     # print(teacher_details)
    #
    #     # for name in teacher_details:
    #     # #print(teacher_details)
    #     #     print(question)
    #
    #
    #     return self.render('admin/test_chart.html')
        # return response

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login',next=request.url))
admin.add_view(ResultsView(name='Results',endpoint='results'))



@admin.teardown_app_request
def close(self):
    db.session.close()
