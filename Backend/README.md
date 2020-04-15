## Backend Architecture
Backend Flask framwork\
Database Postgresql\
Production Server Waitress WSGI Server\

## Python Requirements
tested on python 3.7\
pip3 install flask flask-sqlalchemy flask-cors requests\
pip3 install waitress pandas\
pip3 install psycopg2-binary\

## Postgresql Setup
install postgresql\
change password of postgres user : \passwd postgres\
Modify app.config as :\  
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:PASSWORD@localhost/university_course_db'\
Login to postgres user : sudo -u postgres psql\
create a "university_course_db" using :  create DATABASE university_course_db;\

## Initialize DB
delete all tables in database: \
drop table "course";\
drop table "user";\
Initialize contents of "user.csv" and "course.csv".\

## Word2Vec model
Download the 1.7 gb model from:
https://s3.amazonaws.com/dl4j-distribution/GoogleNews-vectors-negative300.bin.gz
Unzip the file and place the "GoogleNews-vectors-negative300.bin" file into the "/Backend" directory

## Start Server
cd Backend\
sudo python3 waitress_server.py\