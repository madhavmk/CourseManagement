from flask import Flask, jsonify,request, Response
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy

import requests

import csv
import pandas as pd
import json


##############


app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@localhost/university_course_db'
db=SQLAlchemy(app)
CORS(app)
app.debug = True
print('Connected to DB !!')


############


class Course(db.Model):

    course_id = db.Column(db.String, primary_key=True)
    course_title = db.Column(db.String)
    course_description = db.Column(db.String)

    def __init__(self,course_id,course_title,course_description):
        self.course_id=course_id
        self.course_title = course_title
        self.course_description = course_description
    
    def representation(self):
        return list([self.course_id,self.course_title,self.course_description])


class User(db.Model):

    username = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    password = db.Column(db.String)
    enrolled_subjects = db.Column(db.String)

    def __init__(self,username, name, password, enrolled_subjects):
        self.username= username
        self.name= name
        self.password=password
        self.enrolled_subjects=enrolled_subjects
    
    def representation(self):
        return list([self.username, self.name, self.password, self.enrolled_subjects])


############


try:
    Course.__table__.create(db.session.bind)
    print('Created empty Course table')
    with open('course.csv', 'r') as file:
        data_df = pd.read_csv('course.csv')
        for index,row in data_df.iterrows():
            new_area = Course(row['course_id'],row['course_title'], row['course_description'])
            db.session.add(new_area)
    db.session.commit()
    print('Populated Course table')

except:
    print('Skipped Course Table creation')
    pass


try:
    User.__table__.create(db.session.bind)
    print('Created empty User table')
    with open('user.csv', 'r') as file:
        data_df = pd.read_csv('user.csv')
        for index,row in data_df.iterrows():
            if( pd.isna( row['enrolled_subjects'] )):
                new_user = User(row['username'],row['name'], row['password'], "")
            else:
                new_user = User(row['username'],row['name'], row['password'], row['enrolled_subjects'])
            db.session.add(new_user)
    db.session.commit()
    print('Populated User table')

except:
    print('Skipped User Table creation')
    pass


#############


@app.route('/user/<username>', methods=["GET"])
def user_username(username):

    print("SERVING GET '/user/<username>'")
    username=str(username)

    user_dict=dict()

    user_table_result = User.query.filter().all()

    table_result_list = [i.representation() for i in user_table_result]

    table_result_list_username = [i[0] for i in table_result_list]

    if (username not in table_result_list_username ):
        temp_dict=dict()
        temp_dict["status"]=400
        return jsonify(temp_dict)
        #return Response(json.dumps("Username Not Present. Please create a new User !"),status=400)

    index = table_result_list_username.index(username)
    table_result_user = table_result_list[index]

    user_dict["username"] = table_result_user[0]
    user_dict["name"] = table_result_user[1]
    user_dict["password"] = table_result_user[2]
    user_dict["enrolled_subjects"] = table_result_user[3]


    return jsonify(user_dict)
    #return Response(json.dumps(user_dict),status=200)


##############


@app.route('/user/add', methods=["POST"])
def user_add():
    try:
        print("SERVING POST '/user/add'")
        username=str(request.json['username'])
        name=str(request.json['name'])
        password=str(request.json['password'])
        enrolled_subjects=str(request.json['enrolled_subjects'])

        new_user = User(username, name, password, enrolled_subjects)

        db.session.add(new_user)
        db.session.commit()

        temp_dict=dict()
        temp_dict["status"]=200
        return jsonify(temp_dict)

        #return Response(json.dumps("Successfully added new User"),status=200)
    except:
        temp_dict=dict()
        temp_dict["status"]=400
        return jsonify(temp_dict)

        #return Response(json.dumps("That Username is already taken! Please choose another one"),status=400)


############


@app.route('/user/enroll', methods=["POST"])
def user_enroll():
    try:
        print("SERVING POST '/user/enroll'")
        username=str(request.json['username'])
        course_id=str(request.json['course_id'])

        user_to_update=User.query.filter(User.username == username).all()

        if len(user_to_update) == 0:
            temp_dict=dict()
            temp_dict["status"]=400
            return jsonify(temp_dict)
            #return Response(json.dumps("That Username does not exist. Please provide existing username"),status=400)
        
        user_to_update = user_to_update[0]
        if user_to_update.enrolled_subjects == "":
            user_to_update.enrolled_subjects = course_id
        else:
            user_to_update.enrolled_subjects = user_to_update.enrolled_subjects + ";" + course_id

        db.session.commit()

        temp_dict=dict()
        temp_dict["status"]=200
        return jsonify(temp_dict)
        #return Response(json.dumps("Successfully enrolled new Subject to User"),status=200)
    except:
        temp_dict=dict()
        temp_dict["status"]=400
        return jsonify(temp_dict)
        #return Response(json.dumps("Error in SERVING POST '/user/enroll' "),status=400)


############


@app.route('/course/add', methods=["POST"])
def course_add():
    try:
        print("SERVING POST '/course/add'")
        course_id=str(request.json['course_id'])
        course_title=str(request.json['course_title'])
        course_description=str(request.json['course_description'])

        new_course = Course(course_id, course_title, course_description)

        db.session.add(new_course)
        db.session.commit()

        temp_dict=dict()
        temp_dict["status"]=200
        return jsonify(temp_dict)
        #return Response(json.dumps("Successfully added new Course"),status=200)
    except:
        temp_dict=dict()
        temp_dict["status"]=400
        return jsonify(temp_dict)
        #return Response(json.dumps("That Course ID already exists! Please choose another one"),status=400)


############


@app.route('/course/info/enrolled/<username>', methods=["GET"])
def course_info_enrolled(username):

    print("SERVING GET '/course/info/enrolled/<username>'")
    username=str(username)
    
    user_table_result = User.query.filter(User.username == username).all()
    if len(user_table_result) == 0 :
        temp_dict=dict()
        temp_dict["status"]=400
        return jsonify(temp_dict)
    user_table_result = user_table_result[0].representation()
    user_course_enrolled_list = list(user_table_result[3].split(";"))
    print('user course enrolled list ', user_course_enrolled_list)


    course_table_result = Course.query.filter().all()
    course_table_result= [i.representation() for i in course_table_result]
    print("course_table_result ",course_table_result)

    user_course_enrolled_info_list=[]
    for i in course_table_result:
        if i[0] in user_course_enrolled_list:
            #print('i is ',i)
            temp_dict=dict()
            temp_dict["course_id"] = i[0]
            temp_dict["course_title"] = i[1]
            temp_dict["course_description"] = i[2] 
            #user_course_enrolled_info_list.append(json.dumps({"course_id":i[0], "course_title":i[1], "course_description":i[2] }))
            user_course_enrolled_info_list.append(temp_dict)

    print("user_course_enrolled_info_list  ",user_course_enrolled_info_list)

    #return Response(user_course_enrolled_info_list,status=200)
    return jsonify(user_course_enrolled_info_list)


#############


@app.route('/course/info/not_enrolled/<username>', methods=["GET"])
def course_info_not_enrolled(username):

    print("SERVING GET '/course/info/not_enrolled/<username>'")
    username=str(username)

    user_table_result = User.query.filter(User.username == username).all()
    if len(user_table_result) == 0 :
        temp_dict=dict()
        temp_dict["status"]=400
        #return Response(json.dumps("Username Not Present. Please enter valid Username !"),status=400)
        return jsonify(temp_dict)
    user_table_result = user_table_result[0].representation()
    user_course_enrolled_list = list(user_table_result[3].split(";"))
    print('user course enrolled list ', user_course_enrolled_list)


    course_table_result = Course.query.filter().all()
    course_table_result= [i.representation() for i in course_table_result]
    print("course_table_result ",course_table_result)

    user_course_not_enrolled_info_list=[]
    for i in course_table_result:
        if i[0] not in user_course_enrolled_list:
            #print('i is ',i)
            temp_dict=dict()
            temp_dict["course_id"] = i[0]
            temp_dict["course_title"] = i[1]
            temp_dict["course_description"] = i[2] 
            #user_course_not_enrolled_info_list.append(json.dumps({"course_id":i[0], "course_title":i[1], "course_description":i[2] }))
            user_course_not_enrolled_info_list.append(temp_dict)
    print("user_course_not_enrolled_info_list  ",user_course_not_enrolled_info_list)

    #return Response(jsonify(results=user_course_not_enrolled_info_list),status=200)
    return jsonify(user_course_not_enrolled_info_list)

##############  Not yet finished recommender logic!!!!


@app.route('/course/info/recommend/<username>', methods=["GET"])
def course_info_recommend(username):

    print("SERVING GET '/course/info/recommend/<username>'")
    username=str(username)

    user_table_result = User.query.filter(User.username == username).all()
    if len(user_table_result) == 0 :
        temp_dict=dict()
        temp_dict["status"]=400
        return jsonify(temp_dict)
    user_table_result = user_table_result[0].representation()
    user_course_enrolled_list = list(user_table_result[3].split(";"))
    #print('user course enrolled list ', user_course_enrolled_list)


    course_table_result = Course.query.filter().all()
    course_table_result= [i.representation() for i in course_table_result]
    #print("course_table_result ",course_table_result)

    user_course_not_enrolled_info_list=[]
    for i in course_table_result:
        if i[0] not in user_course_enrolled_list:
            #print('i is ',i)
            temp_dict=dict()
            temp_dict["course_id"] = i[0]
            temp_dict["course_title"] = i[1]
            temp_dict["course_description"] = i[2] 
            #user_course_not_enrolled_info_list.append(json.dumps({"course_id":i[0], "course_title":i[1], "course_description":i[2] }))
            user_course_not_enrolled_info_list.append(temp_dict)


    print("user_course_not_enrolled_info_list  ",user_course_not_enrolled_info_list)


    user_course_enrolled_info_list=[]
    for i in course_table_result:
        if i[0] in user_course_enrolled_list:
            #print('i is ',i)
            temp_dict=dict()
            temp_dict["course_id"] = i[0]
            temp_dict["course_title"] = i[1]
            temp_dict["course_description"] = i[2] 
            #user_course_enrolled_info_list.append(json.dumps({"course_id":i[0], "course_title":i[1], "course_description":i[2] }))
            user_course_enrolled_info_list.append(temp_dict)
    print("user_course_enrolled_info_list  ",user_course_enrolled_info_list)

    # # # # Add Recommender logic using user course 'enrolled' and 'not enrolled' information

    #return Response(user_course_not_enrolled_info_list,status=200)
    return jsonify(user_course_not_enrolled_info_list)