
from  .. import db,login_manager
from flask_login import UserMixin,AnonymousUserMixin
from werkzeug.security import generate_password_hash ,check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
import datetime

#TO RETURN ANY VARIABLE FROM THE CHILD OR PARENT TABLE USE THE BACKREF option


class Roles(db.Model):
    __tablename__='roles'
    id=db.Column(db.Integer,primary_key=True)
    role_name=db.Column(db.String(50),unique=True,index=True)

    users=db.relationship('User',backref='role',lazy='dynamic')

    def __str__(self):
        return "%s" %format(self.role_name)

    def __repr__(self):
        return "%r" %self.role_name

teachersubject=db.Table('teachersub',
db.Column('userid',db.Integer,
db.ForeignKey('users.id',ondelete="CASCADE")),

db.Column('subjectid',db.Integer,
db.ForeignKey('subject.id',ondelete="CASCADE")),
db.UniqueConstraint('userid','subjectid'),
db.PrimaryKeyConstraint('userid','subjectid')
)
semesterelective=db.Table('semelect',
db.Column('electiveid',db.Integer,
db.ForeignKey('electives.id',ondelete="CASCADE")),
db.Column('semesterid',db.Integer,
db.ForeignKey('semester.id',ondelete="CASCADE")),
db.PrimaryKeyConstraint('electiveid','semesterid')
)

class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id=db.Column(db.Integer,primary_key=True)
    fname=db.Column(db.String(50),nullable=False,index=True)
    lname=db.Column(db.String(50),nullable=False,index=True)
    password_hash=db.Column(db.String(256),nullable=False)
    email=db.Column(db.String(30),unique=True,nullable=False,index=True)
    created_on=db.Column(db.DateTime,index=True,default=datetime.datetime.utcnow,nullable=False)
    confirmed=db.Column(db.Boolean,default=False)
    # Organization to User
    organization_id=db.Column(db.Integer,db.ForeignKey('organization.id'),nullable=False)

    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'),nullable=False)
    # role_rel=db.relationship('Roles',backref='role',lazy='select')

    #User to Submissions
    user_sub=db.relationship('Submissions',backref='usersub',lazy='dynamic')

    #User many to many with subjects
    # sub_id=db.relationship('Subject',backref=db.backref("teacher_id",
    # lazy="subquery"),lazy="subquery",secondary=teachersubject)
    sub_id=db.relationship('Subject',secondary=teachersubject,
    lazy='dynamic',back_populates="teacher_name",
    )


    #use one to many
    # sub_id=db.relationship('Subject',backref='teacher_id',lazy='dynamic')


    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email==current_app.config["ADMIN_EMAIL"]:
                self.role=Roles.query.filter_by(role_name='admin').first()
            if self.role is None:
                self.role=Roles.query.filter_by(role_name='teacher').first()

    

    @property
    def password(self):
        raise AttributeError("password is readonly")

    @password.setter
    def password(self,password):
       self.password_hash = generate_password_hash(password,method='pbkdf2:sha512',salt_length=64)

        #def set_role(self):


    def verify_password(self,password):
       return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self,expiration=3600):
        s=Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'confirm':self.id}).decode('utf-8')

    def confirm(self,token):

        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False

        self.confirmed=True
        db.session.add(self)
        #db.session.commit()
        return True

    def get_id(self):
        return self.id

    def get_role(self):

        return self.role

    def is_admin(self):
        return True if str(self.role) == 'admin' else False


    def __repr__(self):
        return "{0} {1}".format(self.fname,self.lname)

    def __str__(self):
        return "{0} {1}".format(self.fname,self.lname)



class Questions(db.Model):
    __tablename__='questions'
    id=db.Column(db.Integer,primary_key=True)
    question=db.Column(db.String(500),index=True,nullable=False)

    #from Organization to Questions
    organization_id=db.Column(db.Integer,db.ForeignKey('organization.id'),nullable=False)

    #from Question to Submissions
    question_sub=db.relationship('Submissions',backref='question_sub',lazy='dynamic')

    def __repr__(self):
        return "<Questions %r>" %self.question
    def __str__(self):
        return "%s" %format(self.question)


class Organization(db.Model):
    __tablename__='organization'
    id=db.Column(db.Integer,primary_key=True)
    organization_domain=db.Column(db.String(25),unique=True,nullable=False,index=True)
    date_created=db.Column(db.DateTime,index=True,default=datetime.datetime.utcnow,nullable=False)

    #organization to User

    organization_rel_users=db.relationship('User',backref='organizationid',lazy='dynamic')


    #organization to Question
    organization_rel_questions=db.relationship('Questions',backref='organization_question_id',lazy='dynamic')

    def __repr__(self):
        return "<Organization %r >" % self.organization_domain
    def __str__(self):
        return " %s " % format(self.organization_domain)

class Submissions(db.Model):
    __tablename__='submissions'
    id=db.Column(db.Integer,primary_key=True)
    form_id=db.Column(db.String,index=True)
    submission=db.Column(db.Integer,nullable=False,index=True)
    user_id=db.Column(db.Integer,db.ForeignKey('users.id'),index=True)
    stream_id=db.Column(db.Integer,db.ForeignKey('streams.id'),index=True)
    question_id=db.Column(db.Integer,db.ForeignKey('questions.id'),index=True)
    subject_id=db.Column(db.Integer,db.ForeignKey('subject.id'),index=True)
    suggestions=db.Column(db.Text,index=True)
    date=db.Column(db.Date,index=True,default=datetime.date.today(),nullable=False)
    #date_time=db.Column(db.DateTime,index=True,default=datetime.datetime.utcnow,nullable=False)

    def __repr__(self):
        return "%r" %format(self.submission)
    def __str__(self):
        return "%s" %format(self.submission)


class Subject(db.Model):
    __tablename__='subject'
    id=db.Column(db.Integer,primary_key=True)
    subject_name=db.Column(db.String,index=True,nullable=False,unique=True)

    submission_rel=db.relationship('Submissions',backref='submission_r',lazy='joined')
    # submission_rel=db.relationship('Submissions',foreign_keys=[Submissions.subject_id],
    # backref=db.backref('submission_id',lazy='joined'),lazy='dynamic')
    #add required field

    stream=db.Column(db.Integer,db.ForeignKey('streams.id'))
    semester=db.Column(db.Integer,db.ForeignKey('semester.id'))



    # teacher=db.Column(db.Integer,db.ForeignKey('users.id'))
    # teacher_name=db.relationship('User',backref=db.backref("subject_det",lazy="joined",
    # cascade="all"),lazy="dynamic",secondary=teachersubject,single_parent=True)

    # teacher_name=db.relationship('User',backref=db.backref("subject_det",
    # lazy="subquery"),lazy="subquery",secondary=teachersubject)
    teacher_name=db.relationship('User',secondary=teachersubject,
    lazy='joined',back_populates='sub_id',
    )


    #one to many to electives
    elective_name_id=db.Column(db.Integer,db.ForeignKey('electives.id'),index=True)
    # elective_rel=db.relationship('Electives',lazy='joined')
    def __str__(self):
        return " %s" %self.subject_name
    def __repr__(self):
        return " %r" %self.subject_name

class Stream(db.Model):
    __tablename__='streams'
    id=db.Column(db.Integer,primary_key=True)
    stream=db.Column(db.String(50),index=True,nullable=False,unique=True)

    subjects=db.relationship('Subject',backref='streamsub',lazy='dynamic')

    # submissions_id=db.relationship('Submissions',
    # foreign_keys=[Submissions.stream_id],
    # backref=db.backref('streamid',lazy='joined'),lazy='dynamic')
    submissions_id=db.relationship('Submissions',backref='stsub',lazy='dynamic')
    elective_stream=db.relationship('Electives',backref='stream_elect',lazy='dynamic')

    def __str__(self):
        return "%s" %self.stream
    def __repr__(self):
        return "%r" %self.stream

class Semester(db.Model):
    __tablename__='semester'
    id=db.Column(db.Integer,primary_key=True)
    semester_name=db.Column(db.Integer,unique=True,nullable=False)
    subject_col=db.relationship('Subject',backref='subject_ref',lazy='dynamic')
    # elective_relationship=db.relationship('Electives',backref='elective_semester',lazy='dynamic')
    elective_relationship=db.relationship('Electives',secondary=semesterelective,
    lazy='dynamic',back_populates="semester_id"
    )
    # elective_relationship=db.relationship('Electives',secondary=semesterelective,
    # lazy='subquery',backref=db.backref("elective_rel",lazy='subquery')
    # )
    def __str__(self):
        return "%s" %self.semester_name
    def __repr__(self):
        return "%r" %self.semester_name


class Electives(db.Model):
    __tablename__='electives'
    id=db.Column(db.Integer,primary_key=True)
    elective_name=db.Column(db.Unicode,unique=True,nullable=False)
    subject_relationship=db.relationship('Subject',backref='elective',lazy='subquery')
    # semester_id=db.Column(db.Integer,db.ForeignKey('semester.id'),index=True)
    semester_id=db.relationship('Semester',secondary=semesterelective,
    lazy='joined',back_populates="elective_relationship")
    # semester_id=db.relationship('Semester',secondary=semesterelective,
    # lazy='subquery',backref=db.backref("semester_rel",lazy='subquery')
    # )
    stream=db.Column(db.Integer,db.ForeignKey('streams.id'),index=True)

    def __str__(self):
        return "%s" %self.elective_name
    def __repr__(self):
        return "%r" %self.elective_name



class AnonymousUser(AnonymousUserMixin):
    is_authenticated=False
    def is_admin(self):
        return False

login_manager.anonymous_user = AnonymousUser



@login_manager.user_loader
def load_user(user_id):

    user=User.query.get(int(user_id))



    if not user:
        return

    return user
