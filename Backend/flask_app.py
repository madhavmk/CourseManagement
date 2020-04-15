from flask import Flask, jsonify,request, Response
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy

import requests

import csv
import pandas as pd
import json

import gensim.models.keyedvectors as word2vec
import gensim.downloader as api
from gensim.parsing.preprocessing import remove_stopwords
import numpy as np

from fuzzywuzzy import fuzz
from fuzzywuzzy import process



##############


app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Iusepostgres@321@localhost/university_course_db'
db=SQLAlchemy(app)
CORS(app)
app.debug = True
print('Connected to DB !!')


############
global wv
wv = word2vec.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)
print('Loaded Word2Vec !!')

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
    marks = db.Column(db.String)

    def __init__(self,username, name, password, enrolled_subjects, marks):
        self.username= username
        self.name= name
        self.password=password
        self.enrolled_subjects=enrolled_subjects
        self.marks = marks # Initialize new user marks as empty string
    
    def representation(self):
        return list([self.username, self.name, self.password, self.enrolled_subjects, self.marks])


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
                new_user = User(row['username'],row['name'], row['password'], "", "")
            else:
                new_user = User(row['username'],row['name'], row['password'], row['enrolled_subjects'], row['marks'])
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
    user_dict["marks"] = table_result_user[4]


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
        marks=str(request.json['marks'])

        new_user = User(username, name, password, enrolled_subjects,marks)

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
            user_to_update.marks = "-1"
        else:
            user_to_update.enrolled_subjects = user_to_update.enrolled_subjects + ";" + course_id
            user_to_update.marks = user_to_update.marks + ";" + "-1"

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
    user_marks_course_enrolled_list = list(user_table_result[4].split(";"))
    print('user course enrolled list ', user_course_enrolled_list)



    course_table_result = Course.query.filter().all()
    course_table_result= [i.representation() for i in course_table_result]
    print("course_table_result ",course_table_result)

    enrolled_course_counter=0
    user_course_enrolled_info_list=[]
    for i in course_table_result:
        if i[0] in user_course_enrolled_list:
            #print('i is ',i)
            temp_dict=dict()
            temp_dict["course_id"] = i[0]
            temp_dict["course_title"] = i[1]
            temp_dict["course_description"] = i[2] 
            temp_dict["marks"] = int(user_marks_course_enrolled_list[enrolled_course_counter])
            #user_course_enrolled_info_list.append(json.dumps({"course_id":i[0], "course_title":i[1], "course_description":i[2] }))
            user_course_enrolled_info_list.append(temp_dict)

            enrolled_course_counter = enrolled_course_counter + 1



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

    enrolled_table_result=[]
    for i in course_table_result:
        if i[0] in user_course_enrolled_list:
            enrolled_table_result.append(i)
    print("enrolled_table_result ",enrolled_table_result)

    not_enrolled_table_result=[]
    for i in course_table_result:
        if i[0] not in user_course_enrolled_list:
            not_enrolled_table_result.append(i)
    print("not_enrolled_table_result ",not_enrolled_table_result)

    #wv = api.load('word2vec-google-news-300')
    #wv = word2vec.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)
    #course_names=[i[0] for i in not_enrolled_table_result]
    #course_words=[i[2] for i in not_enrolled_table_result] 

    course_names_enrolled=[i[0] for i in enrolled_table_result]
    course_words_enrolled=[i[2] for i in enrolled_table_result]
    course_names_not_enrolled=[i[0] for i in not_enrolled_table_result]
    course_words_not_enrolled=[i[2] for i in not_enrolled_table_result]



    course_vals = {}    

    def vector(x):
        len_is = 0
        sum_is = 0
        for word in x:
            if word in wv.vocab:
                sum_is = sum_is + wv[word]
                len_is = len_is + 1
        return sum_is / len_is

    def cos(x,y):
        return np.dot(x, y)/(np.linalg.norm(x)* np.linalg.norm(y))

    for i in range(len(course_names_enrolled)):
        get_vector = vector(course_words_enrolled[i])
        course_vals[course_names_enrolled[i]] = get_vector
    for i in range(len(course_names_not_enrolled)):
        get_vector = vector(course_words_not_enrolled[i])
        course_vals[course_names_not_enrolled[i]] = get_vector

    course_not_enrolled_max_dist = []
    for i in range(len(course_names_not_enrolled)):
        max_value=-1
        max_value_index=-1
        for j in range(len(course_names_enrolled)):
            get_sim = cos(course_vals[course_names_not_enrolled[i]],course_vals[course_names_enrolled[j]])
            if get_sim>max_value:
                max_value=get_sim
                max_value_index=j
            print(course_names_not_enrolled[i],' || ',course_names_enrolled[j] ,' = ',get_sim)
        print("MAX  !! ",course_names_not_enrolled[i],' || ',course_names_enrolled[max_value_index] ,' = ',max_value)
        course_not_enrolled_max_dist.append([course_names_not_enrolled[i],course_names_enrolled[max_value_index],max_value])

    def sortCustom(val): 
        return val[2] 
    course_not_enrolled_max_dist = sorted(course_not_enrolled_max_dist, key = sortCustom, reverse=True)

    print('sorted subjects  ',course_not_enrolled_max_dist)

    def findIndex(course_table_result, course_id):
        course_table_result_course_id = [i[0] for i in course_table_result]
        index = course_table_result_course_id.index(course_id)
        return index

    search_course=[]
    for i in course_not_enrolled_max_dist:
        index_course = findIndex(course_table_result, i[0])
        index_related_course = findIndex(course_table_result, i[1])
        temp_dict=dict()
        temp_dict["course_id"] = course_table_result[index_course][0]
        temp_dict["course_title"] = course_table_result[index_course][1]
        temp_dict["course_description"] = course_table_result[index_course][2] 
        temp_dict["related_course_title"] = course_table_result[index_related_course][2]
        search_course.append(temp_dict)

    return jsonify(search_course[0:5])
    

    """

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
    

    # # # # Add Recommender logic using user course 'enrolled' and 'not enrolled' information
    return jsonify(user_course_not_enrolled_info_list)
    """
    
    
#################


@app.route('/user/marks_add', methods=["POST"])
def user_marks_add():
    try:
        print("SERVING POST '/user/marks_add'")
        username=str(request.json['username'])
        course_id=str(request.json['course_id'])
        marks = str(request.json['marks'])

        user_to_update=User.query.filter(User.username == username).all()

        if len(user_to_update) == 0:
            temp_dict=dict()
            temp_dict["status"]=400
            return jsonify(temp_dict)
            #return Response(json.dumps("That Username does not exist. Please provide existing username"),status=400)
        
        user_to_update = user_to_update[0]
        
        current_user_subjects = user_to_update.enrolled_subjects.split(";")
        print('current_user_subjects ',current_user_subjects)
        current_user_marks = user_to_update.marks.split(";")
        print('current_user_marks ',current_user_marks)

        if course_id not in current_user_subjects:
            temp_dict=dict()
            temp_dict["status"]=400
            return jsonify(temp_dict)  

        index = current_user_subjects.index(course_id)
        print('index ',index)

        current_user_marks[index] = marks

        new_user_marks = ";".join(current_user_marks)
        print("new_user_marks ",new_user_marks)

        user_to_update.marks = new_user_marks

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



@app.route('/course/info/search/<username>/<phrase>', methods=["GET"])
def course_info_search(username,phrase):

    print("SERVING GET '/course/info/search/<username>/<phrase>'")
    username=str(username)
    phrase=str(phrase)

    user_table_result = User.query.filter(User.username == username).all()
    if len(user_table_result) == 0 :
        temp_dict=dict()
        temp_dict["status"]=400
        return jsonify(temp_dict)
    user_table_result = user_table_result[0].representation()
    user_course_enrolled_list = list(user_table_result[3].split(";"))

    course_table_result = Course.query.filter().all()
    course_table_result= [i.representation() for i in course_table_result]

    not_enrolled_table_result=[]
    for i in course_table_result:
        if i[0] not in user_course_enrolled_list:
            not_enrolled_table_result.append(i)
    print("not_enrolled_table_result ",not_enrolled_table_result)

    course_names_not_enrolled=[i[0] for i in not_enrolled_table_result]
    course_words_not_enrolled=[i[1] for i in not_enrolled_table_result]#####
    print('course_words_not_enrolled ',course_words_not_enrolled)

    """
    course_vals = {}    

    def vector(x):
        len_is = 0
        sum_is = 0
        for word in x:
            if word in wv.vocab:
                sum_is = sum_is + wv[word]
                len_is = len_is + 1
        return sum_is / len_is

    def cos(x,y):
        return np.dot(x, y)/(np.linalg.norm(x)* np.linalg.norm(y))

    for i in range(len(course_names_not_enrolled)):
        get_vector = vector(course_words_not_enrolled[i])
        course_vals[course_names_not_enrolled[i]] = get_vector

    course_vals[phrase] = vector(phrase)
    """
    course_not_enrolled_max_dist = []
    for i in range(len(course_names_not_enrolled)):
        
        #get_sim = cos(course_vals[course_names_not_enrolled[i]],course_vals[phrase])
        get_sim = fuzz.token_sort_ratio(course_words_not_enrolled[i],phrase)
        print(course_names_not_enrolled[i],' || ',phrase ,' = ',get_sim)
   
        course_not_enrolled_max_dist.append([course_names_not_enrolled[i],phrase,get_sim])


    def sortCustom(val): 
        return val[2] 
    course_not_enrolled_max_dist = sorted(course_not_enrolled_max_dist, key = sortCustom, reverse=True)

    print('sorted subjects  ',course_not_enrolled_max_dist)

    def findIndex(course_table_result, course_id):
        course_table_result_course_id = [i[0] for i in course_table_result]
        index = course_table_result_course_id.index(course_id)
        return index

    search_course=[]
    for i in course_not_enrolled_max_dist:
        index_course = findIndex(course_table_result, i[0])
        temp_dict=dict()
        temp_dict["course_id"] = course_table_result[index_course][0]
        temp_dict["course_title"] = course_table_result[index_course][1]
        temp_dict["course_description"] = course_table_result[index_course][2] 
        search_course.append(temp_dict)

    return jsonify(search_course[0:3])



################
"""


@app.route('/course/info/search/<username>/<phrase>', methods=["GET"])
def course_info_search(username,phrase):

    print("SERVING GET '/course/info/search/<username>/<phrase>'")
    username=str(username)
    phrase=str(phrase)

    user_table_result = User.query.filter(User.username == username).all()
    if len(user_table_result) == 0 :
        temp_dict=dict()
        temp_dict["status"]=400
        return jsonify(temp_dict)
    user_table_result = user_table_result[0].representation()
    user_course_enrolled_list = list(user_table_result[3].split(";"))

    course_table_result = Course.query.filter().all()
    course_table_result= [i.representation() for i in course_table_result]

    not_enrolled_table_result=[]
    for i in course_table_result:
        if i[0] not in user_course_enrolled_list:
            not_enrolled_table_result.append(i)
    print("not_enrolled_table_result ",not_enrolled_table_result)

    course_names_not_enrolled=[i[0] for i in not_enrolled_table_result]
    course_words_not_enrolled=[i[1] for i in not_enrolled_table_result]#####
    print('course_words_not_enrolled ',course_words_not_enrolled)

    course_vals = {}    

    def vector(x):
        len_is = 0
        sum_is = 0
        for word in x:
            if word in wv.vocab:
                sum_is = sum_is + wv[word]
                len_is = len_is + 1
        return sum_is / len_is

    def cos(x,y):
        return np.dot(x, y)/(np.linalg.norm(x)* np.linalg.norm(y))

    for i in range(len(course_names_not_enrolled)):
        get_vector = vector(course_words_not_enrolled[i])
        course_vals[course_names_not_enrolled[i]] = get_vector

    course_vals[phrase] = vector(phrase)

    course_not_enrolled_max_dist = []
    for i in range(len(course_names_not_enrolled)):
        
        get_sim = cos(course_vals[course_names_not_enrolled[i]],course_vals[phrase])
        print(course_names_not_enrolled[i],' || ',phrase ,' = ',get_sim)
   
        course_not_enrolled_max_dist.append([course_names_not_enrolled[i],phrase,get_sim])


    def sortCustom(val): 
        return val[2] 
    course_not_enrolled_max_dist = sorted(course_not_enrolled_max_dist, key = sortCustom, reverse=True)

    print('sorted subjects  ',course_not_enrolled_max_dist)

    def findIndex(course_table_result, course_id):
        course_table_result_course_id = [i[0] for i in course_table_result]
        index = course_table_result_course_id.index(course_id)
        return index

    search_course=[]
    for i in course_not_enrolled_max_dist:
        index_course = findIndex(course_table_result, i[0])
        temp_dict=dict()
        temp_dict["course_id"] = course_table_result[index_course][0]
        temp_dict["course_title"] = course_table_result[index_course][1]
        temp_dict["course_description"] = course_table_result[index_course][2] 
        search_course.append(temp_dict)

    return jsonify(search_course[0:3])

"""
#########