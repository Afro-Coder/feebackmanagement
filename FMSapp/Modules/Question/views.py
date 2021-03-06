from . import question
from flask import request,render_template,url_for,redirect,flash,jsonify,abort
from ...models.users import User,Stream,Subject,Questions,Submissions
from .forms import QuestionSelect,QuestionForm,QuestionRadio
from ...mod_util import decode_hashid
from wtforms.validators import ValidationError
from flask import session
from FMSapp import db
from FMSapp.Modules.utils import generate_form_token
from sqlalchemy import or_

#add a url converter here
# @question.before_request
# def before_req():
#     pass


@question.route('/stream/red/<hashid>/<semester>',methods=['GET'])
def question_red(hashid,semester):
    #find the referrer using url for refer to auth login
    # print(request.url_root[7:])
    # print(request.endpoint)


    return render_template('question/ques_redirect.html',hashid=hashid,semester=semester)

    # return redirect(url_for('.display_question',hashid=hashid,semester=semester))
@question.route("/stream/<hashid>/<semester>", methods=['GET', 'POST'])
def display_question(hashid,semester):
    if request.referrer is None:
        return redirect(url_for('.question_red',hashid=hashid,semester=semester))

    try:

        dec=decode_hashid(hashid=hashid)
        # if  not dec:
        #     abort(404)
        print("semester {0}".format(dec))
        (dec,)=dec
        stream_id=dec


        dec1=decode_hashid(hashid=semester)
        print("semester"+str(dec1))
        (dec1,)=dec1
        semester_id=dec1
        print("SEMESTER {0}".format(semester_id))

    except Exception as e:
        print(e)
        abort(404)

    # if request.args.get('elective',0,type=int))
    elective=request.args.get('elective',type=int)
    # print(semester_id)
    # print(elective)
    #
    #     elective_search
    # subjects= Subject.query.filter_by(stream=dec,semester=dec1)

    filters=[
    Subject.stream==dec,
    Subject.semester==dec1,

    ]
    # print(*filters)
    subjects= Subject.query.filter(*filters).filter(or_(\
    Subject.elective_name_id==elective,Subject.elective_name_id.is_(None)))

    question=[(ques.id,ques.question) for ques in Questions.query.all()]
    form=QuestionSelect()
    form.subject_data.query=subjects
    # form.teacher_select.choices={('__None','Select a Teacher')}
    form.teacher_select.choices=[]

    # if form.validate_on_submit():
    #     print("\t\t\t\t TRUE")
    #     return "Success"

    form_id=generate_form_token(12)
    # session["form_id"]=form_id
    # print(request.endpoint)
    return render_template('question/question_display.html',form=form,question=question,hashid=hashid,form_id=form_id)


@question.route('/_gen_teachers',methods=['GET','POST'])
def gen_teacher():

    if request.method == "GET":
        subject_id=request.args.get('b',0,type=int)

        # list.append(subject_id)
        # print(list)
        # print(subject_id)

        t=[(row.id,row.fname+' '+row.lname)  for row in  User.query.filter(User.sub_id.any(id=subject_id)).all()]


        return jsonify(t)

    if request.method == "POST":
        #datasub=Submissions()
        dictv =request.form.to_dict()
        # print(dictv)
        dictv.pop('csrf_token')
        # print("debug")
        # print(dictv)
        d={key[7:]:dictv[key] for key in dictv if key.startswith('options')}
        if not d:
            abort(405)

        # for key,value in d.items():
        #     print(key+":::"+value)

        print(dictv)
        stream=decode_hashid(dictv["stream_id"])
        (stream,)=stream

        # if session["form_id"] != dictv["form_id"]:
        #     return False
        # session["dict_form_id"]=dictv["form_id"]
        # print("\t\t\After Posting",session["dict_form_id"])
        #
        try:
            print('s')
            for key,value in d.items():
                datasub=Submissions()

                datasub.form_id=dictv["form_id"]
                datasub.user_id=int(dictv["teacher_select"])
                datasub.subject_id=int(dictv["subject_data"])
                datasub.stream_id=int(stream)
                datasub.question_id=int(key)
                datasub.submission=int(value)

                if key == "1":
                    datasub.suggestions=dictv["suggestions"]
                db.session.add(datasub)
            db.session.commit()



        except Exception as e:
            print('error'.format(e))
            db.session.rollback();


        # for key,value in dictv.items():
        #     print(key[-1:]+"::"+value)

        # print(dictv)
        # print("success")
        jsondata=[{'type':'success','message':'success'}]
        return jsonify(jsondata)

    return(jsonify({'message':'Error please contact admin'}))




        # t={(row.fname,row.teacherid.__dict__) for row in User.query.join(User.subjectid).filter(User.id==Subject.id)}
        # print(p)
        # print(t)
@question.route('/success')
def suc():
    if request.referrer is None:

        abort(404)
    return render_template("question/success.html")



# @question.route('/test_question',methods=["GET","POST"])
# def testques():
#
#     question=[(ques.id,ques.question) for ques in Questions.query.all()]
#     #form=QuestionForm()
#
#     # print(question)
#
#     form=QuestionForm()
#     form.options.append_entry(RadioField("ra"))
#     #test=[a for a in dir(form.options) if not a.startswith('__')]
#     #print(test)
#
#     return render_template('question/questiondisp.html',form=form,question=question)
# @question.route('/_subform',methods=["GET","POST"])
# def subform():
#     print("Hello")
#     dictv = request.form.to_dict()
#     print(dictv)
#     dictv.pop('csrf_token')
#     print(dictv)
#     d={key[-1:]:dictv[key] for key in dictv if key.startswith('options')}
#     # print(d)
#     # # for key in dict:
#     #     # print(key.startswith('options'))
#     #     # print("\n")
#     #     # print('form key '+dict[key])
#
#     return "Sucess"
