from flask import Flask, request, jsonify, request,render_template,redirect
from flask_pymongo import PyMongo
from pymongo import UpdateOne
from bson import ObjectId
from bson import json_util
from datetime import datetime, timedelta
from bson.json_util import dumps
import json
import random
import string
import os
import datetime


app = Flask(__name__)

app.config['MONGO_URI'] = 'mongodb://localhost:27017/Quizes'
mongo_q = PyMongo(app)

app.config["MONGO_URI"] = "mongodb://localhost:27017/Students"
mongo_s = PyMongo(app)

app.config['MONGO_URI'] = 'mongodb://localhost:27017/Parents'
mongo_p = PyMongo(app)

app.config['MONGO_URI'] = 'mongodb://localhost:27017/Teachers'
mongo_t = PyMongo(app)


# API's supporter functions
def get_entities(collection_name, dbinitialize):
    all_entities = list(dbinitialize.db[collection_name].find())
    return jsonify(all_entities)

def got_entities(collection_name, dbinitialize):
    all_entities = list(dbinitialize.db[collection_name].find())
    return (json_util.dumps(all_entities))


def get_filtered(collection_name, dbinitialize):
    all_entities = list(dbinitialize.db[collection_name].find())
    return (all_entities)

def get_entity(collection_name, entity_id, dbinitialize):
    entity = dbinitialize.db[collection_name].find_one({"_id": entity_id})
    return entity


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'jfif'}  # Allowed file extensions for images 
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_student(user_id):
    user = mongo_s.db.student_profile.find_one({'user_id': user_id})
    if user:
        user['_id'] = str(user['_id'])  # Convert ObjectId to a string
    return (user)

def got_collection(role):
    if role == 'student':
        return mongo_s.db
    elif role == 'parent':
        return mongo_p.db
    elif role == 'teacher':
        return mongo_t.db
    else:
        raise ValueError("Invalid collection name")


def get_collection(role):
    if role == 'student':
        return mongo_s.db['quiz_data']
    elif role == 'parent':
        return mongo_p.db['quiz_data']
    elif role == 'teacher':
        return mongo_t.db['quiz_data']
    else:
        raise ValueError("Invalid collection name")


# Define the folder where uploaded images will be stored
app.config['UPLOAD_FOLDER'] = 'uploads'


# @app.route('/upload_image', methods=['POST'])
def upload_image(image):
    # image = request.files.get('image')
    if image and allowed_file(image.filename):
        filename = f"{ObjectId()}.{image.filename}"
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"message": "Image uploaded successfully.", "filename": filename}), 200
    else:
        return jsonify({"message": "Invalid image or file format."}), 400


# Getting all subject 
@app.route('/get_all_subject_quizz', methods = ['GET'])
def get_all_subject_quizz():
    return got_entities('quizz_subjects', mongo_q)

# Getting topic of selected subject 
@app.route('/get_subject_topics/<string:subject>', methods = ['GET'])
def get_subject_topics(subject):
    All_topics = mongo_q.db.quizz_subjects.find_one({'subject':subject})
    topics = [i for i in All_topics['topics'] ]
    return (topics)

# Getting subtopics of selected subject and topic
@app.route('/get_subject_subtopics/<string:subject>/<string:topics>', methods = ['GET'])
def get_subject_subtopics(subject,topics):
    All_subtopics = mongo_q.db.quizz_subjects.find_one({'subject':subject})
    subtopics = All_subtopics['topics'][topics]
    return jsonify(subtopics)


# Create and update a route to add subjects, topics, or subtopics
@app.route('/add_Subject_quizz', methods=['POST'])
def add_Subject_quizz():
    subject_name = request.form.get('subject')
    subject_document = mongo_q.db.quizz_subjects.find_one({'subject': subject_name})
    
    if subject_document is None:
        # Subject doesn't exist in the database, create it
        subject_document = {'subject': subject_name, 'topics': {}}
        mongo_q.db.quizz_subjects.insert_one(subject_document)

    topic_name = request.form.get('topic')
    subtopic_name = request.form.get('subtopic')

    if topic_name:
        if topic_name not in subject_document['topics']:
            subject_document['topics'][topic_name] = []  # Create an empty list for subtopics
            # Update the subject document in the database to include the new topic
            mongo_q.db.quizz_subjects.update_one({'subject': subject_name}, {'$set': {'topics': subject_document['topics']}})

    if subtopic_name:
        if not topic_name:
            return jsonify({"message": "Cannot add subtopic without a topic."}), 400

        if topic_name not in subject_document['topics']:
            return jsonify({"message": "Topic does not exist in the subject."}), 400

        # Check if the subtopic already exists in the topic's subtopics
        if subtopic_name not in subject_document['topics'][topic_name]:
            subject_document['topics'][topic_name].append(subtopic_name)
            # Update the subject document in the database to include the new subtopic
            mongo_q.db.quizz_subjects.update_one({'subject': subject_name}, {'$set': {'topics': subject_document['topics']}})

    return jsonify({"message": "Data added successfully."}), 200


# Get all quizes
@app.route('/get_all_quizz', methods = ['GET'])
def get_all_quizz():
    return get_entities('quizes', mongo_q)

# Get single quiz using its id
@app.route('/get_quizz/<string:quiz_id>', methods = ['GET'])
def get_quizz(quiz_id):
    return get_entity('quizes', quiz_id, mongo_q)

# Create new Quiz requires creator user id
@app.route('/create_quiz/<string:creator_id>', methods=['GET', 'POST'])
def create_quiz(creator_id):
    if request.method == 'GET':
        return render_template("index.html",creator_id=creator_id)
    elif request.method == 'POST':
        try:
            language = request.form.get('language')
            class_name = request.form.get('class')
            subject = request.form.get('subject')
            topic = request.form.get('topic')
            subtopic = request.form.get('subtopic')
            level = request.form.get('level')
            quiz_type = request.form.get('quiz_type')
            # Get question container data
            question = request.form.get('question')
            question_image = request.files.get('question_image')
            correct_option = request.form.get('correct_option')
            question_image_url = None

            if question_image and allowed_file(question_image.filename):
                try:
                    filename = f"{ObjectId()}.{question_image.filename}"
                    question_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    question_image_url = filename 
                except Exception as e:
                    return jsonify({"message": "Error uploading question image.", "error": str(e)}), 500
            
            options = []
            i = 1
            while True:
                option_text = request.form.get(f'option_{i}')
                option_image = request.files.get(f'option_{i}_image')
                option_image_url = None
                if not option_text:  # If option_text is empty, exit the loop
                    break
                
                if option_image and allowed_file(option_image.filename):
                    try:
                        # Save the option image to the 'uploads' folder
                        filename = f"{ObjectId()}.{option_image.filename}"
                        option_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        option_image_url = filename  # Store the file path in the database

                    except Exception as e:
                        return jsonify({"message": f"Error uploading option {i} image.", "error": str(e)}), 500
                    
                option_data = {
                    'text': option_text,
                    'image_url': option_image_url,
                    'is_answer': request.form.get(f'is_answer_{i}') == 'true'
                }

                options.append(option_data)

                i += 1  # Increment the option counter


            new_quiz = {
                "_id": str(ObjectId()),
                "creator_id": creator_id,
                "quizz_add_time": datetime.datetime.now(),
                "language": language,
                "class": class_name,
                "subject": subject,
                "topic": topic,
                "subtopic": subtopic,
                "level": level,
                "quiz_type": quiz_type,
                'question_container': {
                    'question': question,
                'question_image_url': question_image_url,
                'options': options,
                'correct_option':correct_option
                },
                "blocked": False   # if it is False, then show to all, if True then hide from everybody also from creator
            }
            # print(new_quiz)

            inserted_result = mongo_q.db.quizes.insert_one(new_quiz)
            inserted_id = inserted_result.inserted_id
            inserted = mongo_q.db.quizes.find_one({"_id": inserted_id})
            response_data = {"message": "Quiz created successfully", "_id": str(inserted["_id"])}
            return jsonify(response_data), 201


        except Exception as e:
            return jsonify({"message": "An error occurred.", "error": str(e)}), 500



# Update quiz requires quiz id and creator id
@app.route('/update_quizz/<string:quiz_id>/<string:creator_id>', methods=['PUT'])
def update_quizz(quiz_id, creator_id):
    try:
        quiz = mongo_q.db.quizes.find_one({"_id": quiz_id})

        if quiz:
            if quiz["creator_id"] != creator_id:
                return jsonify({"message": "Unauthorized access. You do not have permission to update this quiz."}), 403

            # Get the updated quiz data from the request
            updated_data = request.form  # Assuming JSON data is sent in the request

            # Update language, class, subject, topic, subtopic, level, and quiz_type if provided
            if 'language' in updated_data:
                quiz["language"] = updated_data['language']
            if 'class' in updated_data:
                quiz["class"] = updated_data['class']
            if 'subject' in updated_data:
                quiz["subject"] = updated_data['subject']
            if 'topic' in updated_data:
                quiz["topic"] = updated_data['topic']
            if 'subtopic' in updated_data:
                quiz["subtopic"] = updated_data['subtopic']
            if 'level' in updated_data:
                quiz["level"] = updated_data['level']
            if 'quiz_type' in updated_data:
                quiz["quiz_type"] = updated_data['quiz_type']

            # Update question, question_image_url, and options if provided
            if 'question_container' in updated_data:
                question_container = updated_data['question_container']

                if 'question' in question_container:
                    quiz["question_container"]["question"] = question_container['question']

                if 'question_image_url' in question_container:
                    quiz["question_container"]["question_image_url"] = question_container['question_image_url']

                if 'options' in question_container:
                    options = []

                    for opt in question_container['options']:
                        # Here, we assume that 'text' and 'is_answer' are always present
                        option_data = {
                            'text': opt['text'],
                            'is_answer': opt['is_answer']
                        }

                        # Check if 'image_url' is provided
                        if 'image_url' in opt:
                            option_data['image_url'] = opt['image_url']

                        options.append(option_data)

                    quiz["question_container"]["options"] = options

            # Save the updated quiz
            mongo_q.db.quizes.replace_one({"_id": quiz_id}, quiz)

            return jsonify({"message": "Quiz updated successfully."}), 200

        else:
            return jsonify({"message": "Quiz not found."}), 404

    except Exception as e:
        return jsonify({"message": "An error occurred.", "error": str(e)}), 500



# Delete quiz requires quiz id and creator id, we are not deleting quiz for real we just make it to not show to any one
@app.route('/delete_quizz/<string:quiz_id>/<string:creator_id>', methods = ['DELETE'])
def delete_quizz(quiz_id, creator_id):
    try:
        result = mongo_q.db.quizes.find_one({"_id": quiz_id})
        if result:
            if result["creator_id"] == creator_id:
                mongo_q.db.quizes.update_one({"_id": quiz_id}, {"$set": {"blocked": True}})
                return jsonify({"message": "Quiz deleted successfully."}), 200
            else:
                return jsonify({"message": "Unauthorized access. You do not have permission to delete this quiz."}), 403
        else:
            return jsonify({"message": "Quiz not found."}), 404
    except Exception as e:
        return jsonify({"message": "An error occurred.", "error": str(e)}), 500


# Get filtered quiz for sessions
@app.route('/get_filtered_quiz/<role>/<user_id>/<subject>/<topic>/<subtopic>/<level>', methods=['GET'])
def get_filtered_quiz( role, user_id, subject, topic, subtopic, level):
    
    quiz_collection = get_collection(role)
    user_quiz_document  = quiz_collection.find_one({'user_id': user_id})

    quiz_collect = mongo_q.db['quizes']
    filter_criteria = {
        'subject': subject,
        'topic': topic,
        'subtopic': subtopic,
        'level': level,
    }
    quizes_bunch = quiz_collect.find(filter_criteria)
    
    attempted_quiz = {entry['quiz_id'] for entry in user_quiz_document.get('quiz_data', [])}   
    non_attempted = [quiz for quiz in quizes_bunch if quiz['_id'] not in attempted_quiz]
    l = []
    for q in non_attempted:
        quiz_id = q.get('_id','' )
        q_container = q.get('question_container', {})  # Use get to safely access q_container
        question = q_container.get('question', '')
        options = q_container.get('options', [])
        correct_option = q_container.get('correct_option', '')  # Use get to safely access correct_option
        l.append({
            'quiz_id':quiz_id,
            'question': question,
            'options': options,
            'correct_option': correct_option
        })

    return jsonify({'list_of_quiz': l})


# # setting status of quiz after click by user on quiz 
@app.route('/setting_status/<string:role>/<string:quiz_id>/<string:_id>', methods=['PUT'])
def setting_status_of_quiz(role, quiz_id, _id):
    try:
        # Get the appropriate collection based on the user's role
        quiz_collection = got_collection(role)

        if role == 'student':
            collection = mongo_s.db['student_profile']
            user_document = collection.find_one({'_id': _id})
            if user_document:
                user_id = user_document["user_id"]
        elif role == 'teacher':
            collection = mongo_t.db['teacher_profile']
            user_document = collection.find_one({'_id': ObjectId(_id)})
            if user_document:
                user_id = user_document["profile"]["useridname_password"]["userid_name"]
        elif role == 'parent':
            collection = mongo_p.db['parent_profile']
            user_document = collection.find_one({'_id': ObjectId(_id)})
            if user_document:
                user_id = user_document["parent_useridname"]
        else:
            return jsonify({"error": "Invalid role."}), 400

        # Check if the user exists
        if not user_document:
            return jsonify({"error": f"{role} not found."}), 404


        # user_id = user_document['user_id']

        # Check if the quiz_data collection exists; if not, create it for the user role
        if 'quiz_data' not in quiz_collection.list_collection_names():
            quiz_collection.create_collection('quiz_data')

        # Find the quiz document by user_id
        quiz_document = quiz_collection['quiz_data'].find_one({'user_id': user_id})
        if quiz_document is None:
            # If the user's quiz data document doesn't exist, create it
            new_quiz_data = {
                "user_id": user_id,
                "quiz_data": []
            }
            quiz_collection['quiz_data'].insert_one(new_quiz_data)
            quiz_document = new_quiz_data  # Assign the newly created document

        # Check if the user has already seen the quiz
        quiz_entry = next((entry for entry in quiz_document['quiz_data'] if entry['quiz_id'] == quiz_id), None)

        if quiz_entry is None:
            # If the user has not seen the quiz, add a new entry for the quiz
            new_quiz_entry = {
                "quiz_id": quiz_id,
                "status": "seen",
                "bookmarked": False
            }
            quiz_document['quiz_data'].append(new_quiz_entry)
            quiz_collection['quiz_data'].update_one({'user_id': user_id}, {"$set": {'quiz_data': quiz_document['quiz_data']}})
            return f"{role} has seen the quiz", 200
        else:
            # If the user has seen the quiz, return an appropriate message
            return "You have already attempted this question.", 200

    except Exception as e:
        return jsonify({"error": "An error occurred.", "details": str(e)}), 500
 


#for bookmark quiz
@app.route('/toggle_bookmark/<string:role>/<string:quiz_id>/<string:user_id>', methods=['POST','PUT'])
def toggle_bookmark(role, quiz_id, user_id):
    try:
        # Get the appropriate collection based on the user's role
        quiz_collection = get_collection(role)

        if role == 'student':
            collection = mongo_s.db['student_profile']
            user_id_field = 'user_id'
        elif role == 'teacher':
            collection = mongo_t.db['teacher_profile']
            user_id_field = 'profile.useridname_password.userid_name'
        elif role == 'parent':
            collection = mongo_p.db['parent_profile']
            user_id_field = 'parent_useridname'
        else:
            return jsonify({"error": "Invalid role."}), 400

        # Check if the user exists
        user_document = collection.find_one({user_id_field: user_id})
        if not user_document:
            return jsonify({"error": f"{role} not found."}), 404
        
        # Check if the quiz_data collection exists; if not, create it
        if 'quiz_data' not in mongo_s.db.list_collection_names():
            mongo_s.db.create_collection('quiz_data')

        # Find the quiz document by user_id
        quiz_document = quiz_collection.find_one({'user_id': user_id})

        if quiz_document is None:
            # If the user's quiz data document doesn't exist, create it
            new_quiz_data = {
                "user_id": user_id,
                "quiz_data": []
            }
            quiz_collection.insert_one(new_quiz_data)
            quiz_document = new_quiz_data  # Assign the newly created document

        # Check if the user has already seen the quiz
        quiz_entry = next((entry for entry in quiz_document['quiz_data'] if entry['quiz_id'] == quiz_id), None)

        if quiz_entry is None:
            # If the user has not seen the quiz, add a new entry for the quiz with "bookmarked" status as provided in the request
            # Assuming that the request includes a JSON body with a "bookmarked" key
            request_data = request.get_json()
            is_bookmarked = request_data.get("bookmarked", False)  # Default is False if not provided in the request
            new_quiz_entry = {
                "quiz_id": quiz_id,
                "status": "seen",
                "bookmarked": is_bookmarked
            }
            quiz_document['quiz_data'].append(new_quiz_entry)
            quiz_collection.update_one({'user_id': user_id}, {"$set": {'quiz_data': quiz_document['quiz_data']}})
            return f"{role} has seen the quiz", 200
        else:
            # I f the user has seen the quiz, update the bookmark status to the provided value
            request_data = request.get_json()
            is_bookmarked = request_data.get("bookmarked", False)  # Default is False if not provided in the request
            quiz_entry['bookmarked'] = is_bookmarked
            quiz_collection.update_one({'user_id': user_id, 'quiz_data.quiz_id': quiz_id}, {"$set": {'quiz_data.$.bookmarked': is_bookmarked}})
            return f"{role} has updated the bookmark status for the quiz", 200
        

    except Exception as e:
        return jsonify({"error": "An error occurred.", "details": str(e)}), 500


# getting   non_repeated  questions for quiz  
@app.route('/get_non_repeated_quiz/<string:role>/<string:_id>', methods=['GET'])
def get_non_repeated_quiz(role, _id):
    
    if role == 'student':
        collection = mongo_s.db['student_profile']
        user_data = collection.find_one({'_id': _id})
        if user_data:
            user_id = user_data["user_id"]
    elif role == 'teacher':
        collection = mongo_t.db['teacher_profile']
        user_data = collection.find_one({'_id': ObjectId(_id)})
        if user_data:
            user_id = user_data["profile"]["useridname_password"]["userid_name"]
    elif role == 'parent':
        collection = mongo_p.db['parent_profile']
        user_data = collection.find_one({'_id': ObjectId(_id)})
        if user_data:
            user_id = user_data["parent_useridname"]
    else:
        return jsonify({"error": "Invalid role."}), 400


    if user_data:
        attempted_quiz = [quiz_data['quiz_id'] for quiz_data in user_data.get('quiz_data', [])]
        
        # Limit the number of questions to 20
        non_attempted = mongo_q.db.quizes.find({'_id': {'$nin': attempted_quiz}}).limit(20)
        l = []

        for quiz in non_attempted:
            q_container = quiz.get('question_container')  # Use get to safely access the dictionary
            if q_container:
                question_id = str(quiz['_id'])
                question = q_container.get('question', '')  # Use get to safely access the dictionary
                options = q_container.get('options', [])
                correct_option = q_container.get('correct_option', '')  # Use get to safely access the dictionary

                l.append({
                    'user_id': user_id,
                    'question_id': question_id,
                    'question': question,
                    'options': options,
                    'correct_option': correct_option
                })


        return jsonify({'list_of_non_rep_ques': l})
    else:
        return jsonify({'message': 'User not found'})
    

#save quiz_data and add points 
@app.route('/update_quiz_data/<string:role>/<quiz_id>/<_id>/<result>/<click>', methods=['PUT'])
def update_quiz_data(role, quiz_id, _id, result, click):
    student_projection = {
        "_id": 1,  # Include ObjectId
        "user_id": 1,  # Include userid_name
        "user_class": 1,  # Include user_image
        "role": 1
    }

    parent_projection = {
        "_id": 1,  # Include ObjectId
        "parent_useridname": 1,  # Include userid_name
        "role": 1  # Include points
    }

    teachers_projection = {
        "_id": 1,
        "profile.useridname_password.userid_name": 1,
        "role": 1
    }
    
    try:
        quiz_collection = get_collection(role)

        if role == 'student':
            collection = mongo_s.db['student_profile']
            user_document = collection.find_one({'_id': _id})
            if user_document:
                user_id = user_document["user_id"]
        elif role == 'teacher':
            collection = mongo_t.db['teacher_profile']
            user_document = collection.find_one({'_id': ObjectId(_id)})
            if user_document:
                user_id = user_document["profile"]["useridname_password"]["userid_name"]
        elif role == 'parent':
            collection = mongo_p.db['parent_profile']
            user_document = collection.find_one({'_id': ObjectId(_id)})
            if user_document:
                user_id = user_document["parent_useridname"]
        else:
            return jsonify({"error": "Invalid role."}), 400

        if user_document:
            quiz_user = quiz_collection.find_one({'user_id': user_id})

            # Check if the quiz_id already exists in quiz_data
            quiz_entry = next((entry for entry in quiz_user['quiz_data'] if entry.get('quiz_id') == quiz_id), None)

            if quiz_entry:
                quiz_entry['result'] = result
                quiz_entry['clicked_on'] = click
                quiz_entry['timestamp'] = datetime.datetime.now()  # Add current timestamp

                # Update the user's document with the modified quiz_data
                quiz_collection.update_one({"user_id": user_id}, {"$set": quiz_user})

                if result == 'YES':
                    points = quiz_user.get("points", 0)
                    new_points = points + 1
                    # Update the "points" field using the $set operator
                
                quiz_collection.update_one(
                    {'user_id': user_id},
                    {'$set': {'points': new_points}}
                )

                return jsonify({"message": f"{role} quiz data updated successfully."}), 200
            else:
                return jsonify({"error": "Quiz not found in user data."}), 400
        else:
            return jsonify({"error": f"{role} not found."}), 400

    except Exception as e:
        return jsonify({"error": "An error occurred.", "details": str(e)}), 500



#new session for one or more participants
@app.route('/create_new_session/<user_id>/<role>/<session_id>', methods=['POST'])
def create_new_session(user_id, role, session_id):
    try:
        session_collection = mongo_q.db.sessions
        
        if session_collection is None:
            if 'sessions' not in mongo_q.db.list_collection_names():
                mongo_q.db.create_collection('sessions')

        Quiz= []
        Quiz.append({
            'quiz_id':'',
            'result':''
        })
        participants =[]
        participants.append({
                        'user_id':'',
                        'Quiz':Quiz,
                        'points':0
                    })
        
        session_document = {
            "session_id": session_id,
            "host_id": user_id,
            "participants": participants,
            "role": role,
            "total_question": ''
        }
        session_collection.insert_one(session_document)

        return jsonify({"message": "Session created successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# attending quiz and add points in session 
@app.route('/attending_quiz_in_session/<string:session_id>/<user_id>/<quiz_id>/<attempted_option>', methods=['POST'])
def attending_quiz_in_session(session_id,user_id,quiz_id,attempted_option):
    try:
        
        session = mongo_q.db.sessions.find_one({"session_id": session_id})
        quiz_question = mongo_q.db.quizes.find_one({"_id": quiz_id})
        if session and quiz_question:
            
            points=0
            if attempted_option == quiz_question["question_container"]["correct_option"]:
                result = "YES"
                points += 1  
            else:
                result = "NO"

            # Update the session data 
            user_entry = next((friend for friend in session["participants"] if friend["user_id"] == user_id), None)
             # If user doesn't exist,
            if not user_entry:
                user_entry = {
                    "user_id": user_id,
                    "Quiz": [],
                    "points": points  # You may initialize points as needed
                }
                session["participants"].append(user_entry)
            
            else:
                user_entry["points"] += points

            user_entry["Quiz"].append({
                "quiz_id": quiz_id,
                "result": result
            })
            mongo_q.db.sessions.replace_one({"session_id": session_id}, session)
            
            return jsonify({"message": "Quiz result updated successfully", "result": result})

        else:
            return jsonify({"message": "Session or quiz not found"}, 404)

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

#for getting particular session
@app.route('/get_point_per_session/<string:session_id>/<string:user_id>/<role>', methods=['GET'])
def get_point_per_session(session_id, user_id, role):
    try:
        # Get the appropriate collection based on the user's role
        if role == 'student':
            collection = mongo_s.db['student_profile']
        elif role == 'teacher':
            collection = mongo_t.db['teacher_profile']
        elif role == 'parent':
            collection = mongo_p.db['parent_profile']
        else:
            return jsonify({"error": "Invalid role."}), 400

        # Check if the user exists in the respective collection
        user_document = collection.find_one({'user_id': user_id})
        if not user_document:
            return jsonify({"error": f"{role} not found."}), 404

        username = user_document.get('username', '')
        user_image = user_document.get('user_image', '')

        session_data = mongo_q.db.sessions.find_one({'participants.user_id': user_id, 'session_id': session_id})
        if session_data:
            for invited_friend in session_data['participants']:
                if invited_friend['user_id'] == user_id:
                    session_points = invited_friend['points']
                    total_question = session_data.get('total_question', 0)
                    return jsonify({"user_id": user_id, "session_id": session_id, "points": session_points,
                                    "username": username, "user_image": user_image,"total_question":total_question})
            
            return jsonify({"error": "User not found in session data."}), 404
        else:
            return jsonify({"error": "Session data not found."}), 404

    except Exception as e:
        return jsonify({"error": "An error occurred.", "details": str(e)}), 500


#for showing profile image
@app.route("/get_user_image/<string:_id>", methods=["GET"])
def get_user_image(_id):
    student_profile = mongo_s.student_profile.find_one({'_id': _id})
    parent_profile = mongo_p.parent_profile.find_one({'_id': _id})
    teacher_profile = mongo_t.teacher_profile.find_one({'_id': _id})

    if student_profile:
        image_url = student_profile.get('user_image', None)
    elif parent_profile:
        image_url = parent_profile.get('parent_image', None)
    elif teacher_profile:
        image_url = teacher_profile.get('user_image', None)
    else:
        return jsonify({'message': 'User not found.'}), 404

    if image_url:
        return jsonify({'image_url': image_url})
    else:
        return jsonify({'message': 'User has no image.'})


# getting accuracy of student
@app.route('/getting_accuracy/<string:student_id>', methods=['GET'])
def getting_accuracy(student_id):
    try:
        student = mongo_s.db.student_profile.find_one({"_id": student_id})
        result = []
        for res in student.get("quiz_data", []):
            try:
                result.append(res['result'])
            except KeyError:
                # Key 'result' not found in this quiz data, continue to the next iteration
                continue
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "An error occurred.", "error": str(e)}), 500

#for leaderboard
@app.route('/get_leaderboard_data/<user_id>', methods=['GET'])
def get_leaderboard_data(user_id):
    try:
        # Define the fields you want to retrieve for the leaderboard
        quiz_data_retrive_projection = {"user_id": 1, "points": 1}

        # Define projections for each user role
        student_projection = {
            "_id": 1,
            "user_id": 1,
            "user_image": 1,
            "role": 1
        }

        parent_projection = {
            "_id": 1,
            "parent_useridname": 1,
            "parent_image": 1,
            "role": 1
        }

        teachers_projection = {
            "_id": 1,
            "profile.useridname_password.userid_name": 1,
            "user_image": 1,
            "role": 1
        }

        # Fetch data from all three collections with the specified projection
        students_data = list(mongo_s.db.student_profile.find({}, student_projection))

        
        parents_data = list(mongo_p.db.parent_profile.find({}, parent_projection))
        teachers_data = list(mongo_t.db.teacher_profile.find({}, teachers_projection))

        # Fetch points and user_id from each quiz_data collection for students
        students_quiz_data = list(mongo_s.db.quiz_data.find({}, quiz_data_retrive_projection))
        for i in students_quiz_data:  #points
            for j in students_data: 
                if i["user_id"] == j["user_id"]:
                    #check if the points field exist if exist add in the student data dictionary else continue
                    if "points" in i and i["points"] is not None:
                        j["points"] = i["points"]
                    else:
                        continue
        # Fetch points and user_id from each quiz_data collection for parents
        parents_quiz_data = list(mongo_p.db.quiz_data.find({}, quiz_data_retrive_projection))
        for i in parents_quiz_data:
            for j in parents_data:
                if i["user_id"] == j["parent_useridname"]:
                    if "points" in i and i["points"] is not None:
                        j["points"] = i["points"]
                    else:
                        continue
        # Fetch points and user_id from each quiz_data collection for teachers
        teachers_quiz_data = list(mongo_t.db.quiz_data.find({}, quiz_data_retrive_projection))
        for i in teachers_quiz_data:
            for j in teachers_data:
                if i["user_id"] == j["profile"]["useridname_password"]["userid_name"]:
                    if "points" in i and i["points"] is not None:
                        j["points"] = i["points"]
                    else:
                        continue
        # Combine data from all three databases
        all_users = students_data + parents_data + teachers_data
        
        for user in all_users:
            user["_id"] = str(user["_id"])
        # Sort the data list in descending order based on 'points' field
        sorted_data = sorted(all_users, key=lambda x: x.get("points", 0), reverse=True)
        # sorted_data = sorted(all_users, key=lambda x: int(x['points']), reverse=True)

        # Find the 'you' user based on 'user_id'
        you = None
        for user in sorted_data:
            if user["_id"] == user_id:
                you = user

        if you is None:
            return jsonify({"error": "User not found in leaderboard."}), 404
        # Remove users who do not have a "points" field
        sorted_data = [user for user in sorted_data if 'points' in user]

        response_data = {
            "you": you,
            "sorted_data": sorted_data
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": "An error occurred.", "details": str(e)}), 500

#For getting Weekly leaderboard
@app.route('/get_weekly_quiz_results/<host_id>', methods=['GET'])
def get_weekly_quiz_results(host_id):
    try:
        # Get the current date and calculate the date seven days ago
        current_date = datetime.datetime.now()
       
        seven_days_ago = current_date - timedelta(days=7)
        sorted_data=[]
        you=None

        # Initialize a list to collect weekly quiz results
        weekly_results = []
        # Define projections for each user role
        student_projection = {
            "_id": 1,
            "user_id": 1,
            "user_image": 1,
            "role": 1
        }

        parent_projection = {
            "_id": 1,
            "parent_useridname": 1,
            "parent_image": 1,
            "role": 1
        }

        teachers_projection = {
            "_id": 1,
            "profile.useridname_password.userid_name": 1,
            "user_image": 1,
            "role": 1
        }

        # Fetch data from all three collections with the specified projection
        students_data = list(mongo_s.db.student_profile.find({}, student_projection))
        parents_data = list(mongo_p.db.parent_profile.find({}, parent_projection))
        teachers_data = list(mongo_t.db.teacher_profile.find({}, teachers_projection))
        all_users = students_data + parents_data + teachers_data


        # Fetch and process student data
        students = mongo_s.db.quiz_data.find()
        
        for student in students:
            quiz_data = student.get("quiz_data", [])
         
            user_id=student.get("user_id")
        
            
            # Filter quiz data for entries with a timestamp within the past seven days
            weekly_quiz_data = [
                entry for entry in quiz_data
                if entry.get("timestamp") and
                entry["timestamp"] <= current_date and
                entry["timestamp"] >= seven_days_ago
            ]
           

            # Calculate points based on quiz results where result is 'YES'
            points = sum(1 for entry in weekly_quiz_data if entry.get("result") == "YES")
            
            
            # Create a dictionary for the student's weekly data if they earned points
            if points > 0:
                weekly_student_data = {
                    "user_id": user_id,
                    "points": points,
                   
                }
                weekly_results.append(weekly_student_data)

        # Fetch and process teacher data
        teachers = mongo_t.db.quiz_data.find()
        for teacher in teachers:
            user_id = teacher.get("user_id")
            quiz_data = teacher.get("quiz_data", [])
            
            # Filter quiz data for entries with a timestamp within the past seven days
            weekly_quiz_data = [
                entry for entry in quiz_data
                if entry.get("timestamp") and
                entry["timestamp"] <= current_date and
                entry["timestamp"] >= seven_days_ago
            ]

            # Calculate points based on quiz results where result is 'YES'
            points = sum(1 for entry in weekly_quiz_data if entry.get("result") == "YES")
            
            # Create a dictionary for the teacher's weekly data if they earned points
            if points > 0:
                weekly_teacher_data = {
                    "user_id": user_id,
                    "points": points,
                  
                }
                weekly_results.append(weekly_teacher_data)
        

        # Fetch and process parent data
        parents = mongo_p.db.quiz_data.find()
        for parent in parents:
            user_id = parent.get("user_id")
            quiz_data = parent.get("quiz_data", [])
            
            # Filter quiz data for entries with a timestamp within the past seven days
            weekly_quiz_data = [
                entry for entry in quiz_data
                if entry.get("timestamp") and
                entry["timestamp"] <= current_date and
                entry["timestamp"] >= seven_days_ago
            ]

            # Calculate points based on quiz results where result is 'YES'
            points = sum(1 for entry in weekly_quiz_data if entry.get("result") == "YES")
            
            # Create a dictionary for the parent's weekly data if they earned points
            if points > 0:
                weekly_parent_data = {
                    "user_id": user_id,
                    "points": points,
                }
                weekly_results.append(weekly_parent_data)
       
        for i in students_data:
            for j in weekly_results:
                if i["user_id"] == j["user_id"]:
                    if "points" in j and j["points"] is not None:
                        i["points"] = j["points"]
                    else:
                        continue
                    
        for i in parents_data:
            for j in weekly_results:
                if j["user_id"] == i["parent_useridname"]:
                    if "points" in j and j["points"] is not None:
                        i["points"] = j["points"]
                    else:
                        continue
                    
        for i in teachers_data:
            for j in weekly_results:
                if j["user_id"] == i["profile"]["useridname_password"]["userid_name"]:
                    if "points" in j and j["points"] is not None:
                        i["points"] = j["points"]
                    else:
                        continue

            all_users = students_data + parents_data + teachers_data
            for user in all_users:
                user["_id"] = str(user["_id"])
            
            # sorted_data = sorted(all_users, key=lambda x: int(x['points']), reverse=True)
            sorted_data = sorted(all_users, key=lambda x: x.get("points", 0), reverse=True)
            you = None
            for user in sorted_data:
                if user["_id"] == host_id:
                    you = user

            if you is None:
                return jsonify({"error": "User not found in leaderboard."}), 404
            # Remove users who do not have a "points" field
            sorted_data = [user for user in sorted_data if 'points' in user]

        response = {
            "sorted_user": sorted_data,
            "you": you
        }
        

        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#For getting monthly leaderboard
@app.route('/get_monthly_quiz_results/<host_id>', methods=['GET'])
def get_monthly_quiz_results(host_id):
    try:
        # Get the current date and calculate the date seven days ago
        current_date =datetime.datetime.now()
        one_month_ago = current_date - timedelta(days=30)

        # Initialize a list to collect weekly quiz results
        monthly_results = []
        # Define projections for each user role
        student_projection = {
            "_id": 1,
            "user_id": 1,
            "user_image": 1,
            "role": 1
        }

        parent_projection = {
            "_id": 1,
            "parent_useridname": 1,
            "parent_image": 1,
            "role": 1
        }

        teachers_projection = {
            "_id": 1,
            "profile.useridname_password.userid_name": 1,
            "user_image": 1,
            "role": 1
        }

        # Fetch data from all three collections with the specified projection
        students_data = list(mongo_s.db.student_profile.find({}, student_projection))
        parents_data = list(mongo_p.db.parent_profile.find({}, parent_projection))
        teachers_data = list(mongo_t.db.teacher_profile.find({}, teachers_projection))
        all_users = students_data + parents_data + teachers_data


        # Fetch and process student data
        students = mongo_s.db.quiz_data.find()
        for student in students:
            quiz_data = student.get("quiz_data", [])
            user_id=student.get("user_id")
        
            
            # Filter quiz data for entries with a timestamp within the past seven days
            monthly_quiz_data = [
                entry for entry in quiz_data
                if entry.get("timestamp") and
                entry["timestamp"] <= current_date and
                entry["timestamp"] >= one_month_ago
            ]

            # Calculate points based on quiz results where result is 'YES'
            points = sum(1 for entry in monthly_quiz_data if entry.get("result") == "YES")
            
            # Create a dictionary for the student's weekly data if they earned points
            if points > 0:
                monthly_student_data = {
                    "user_id": user_id,
                    "points": points,
                   
                }
                monthly_results.append(monthly_student_data)

        # Fetch and process teacher data
        teachers = mongo_t.db.quiz_data.find()
        for teacher in teachers:
            user_id = teacher.get("user_id")
            quiz_data = teacher.get("quiz_data", [])
            
            # Filter quiz data for entries with a timestamp within the past seven days
            monthly_quiz_data = [
                entry for entry in quiz_data
                if entry.get("timestamp") and
                entry["timestamp"] <= current_date and
                entry["timestamp"] >= one_month_ago
            ]

            # Calculate points based on quiz results where result is 'YES'
            points = sum(1 for entry in monthly_quiz_data if entry.get("result") == "YES")
            
            # Create a dictionary for the teacher's weekly data if they earned points
            if points > 0:
                monthly_teacher_data = {
                    "user_id": user_id,
                    "points": points,
                  
                }
                monthly_results.append(monthly_teacher_data)

        # Fetch and process parent data
        parents = mongo_p.db.quiz_data.find()
        for parent in parents:
            user_id = parent.get("user_id")
            quiz_data = parent.get("quiz_data", [])
            
            # Filter quiz data for entries with a timestamp within the past seven days
            monthly_quiz_data = [
                entry for entry in quiz_data
                if entry.get("timestamp") and
                entry["timestamp"] <= current_date and
                entry["timestamp"] >= one_month_ago
            ]

            # Calculate points based on quiz results where result is 'YES'
            points = sum(1 for entry in monthly_quiz_data if entry.get("result") == "YES")
            
            # Create a dictionary for the parent's weekly data if they earned points
            if points > 0:
                monthly_parent_data = {
                    "user_id": user_id,
                    "points": points,
                }
                monthly_results.append(monthly_parent_data)
    
        for i in students_data:
            for j in monthly_results:
                if i["user_id"] == j["user_id"]:
                    if "points" in j and j["points"] is not None:
                        i["points"] = j["points"]
                    else:
                        continue
                    
        for i in parents_data:
            for j in monthly_results:
                if j["user_id"] == i["parent_useridname"]:
                    if "points" in j and j["points"] is not None:
                        i["points"] = j["points"]
                    else:
                        continue
                    
        for i in teachers_data:
            for j in monthly_results:
                if j["user_id"] == i["profile"]["useridname_password"]["userid_name"]:
                    if "points" in j and j["points"] is not None:
                        i["points"] = j["points"]
                    else:
                        continue

            all_users = students_data + parents_data + teachers_data
            for user in all_users:
                user["_id"] = str(user["_id"])
            
            # sorted_data = sorted(all_users, key=lambda x: int(x['points']), reverse=True)
            sorted_data = sorted(all_users, key=lambda x: x.get("points", 0), reverse=True)
            you = None
            for user in sorted_data:
                if user["_id"] == host_id:
                    you = user

            if you is None:
                return jsonify({"error": "User not found in leaderboard."}), 404
            # Remove users who do not have a "points" field
            sorted_data = [user for user in sorted_data if 'points' in user]

        response = {
            "sorted_user": sorted_data,
            "you": you
        }

        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# invite section 
def search_student(search_value):
    student = mongo_s.db.student_profile.find_one({'user_id': search_value})
    if not student:
        student = mongo_s.db.student_profile.find_one({'personal_info.contact.email': search_value})
    if not student:
        student = mongo_s.db.student_profile.find_one({'personal_info.contact.phone': search_value})
    if student:
        student['_id'] = str(student['_id'])  # Convert ObjectId to string
        data = {
            "_id": student['_id'],
            "role": student['role'],
            "user_id": student['user_id'],
            "username": student['username'],
            "user_image": student['user_image'],
        }
        return data
    return student


#search parent by their unique identity
def search_parent(search_value):
    parent = mongo_p.db.parent_profile.find_one({'parent_useridname': search_value})
    if not parent:
        parent = mongo_p.db.parent_profile.find_one({'personal_info.contact.parent_email': search_value})
    if not parent:
        parent = mongo_p.db.parent_profile.find_one({'personal_info.contact.parent_phone': search_value})
    if parent:
        parent['_id'] = str(parent['_id'])
        data = {
            "_id": parent['_id'],
            "role": parent['role'],
            "user_id": parent['parent_useridname'],
            "username": parent['parent_name'],
            "user_image": parent['parent_image']
        }
        return data
    return parent

#search teacher by their unique identity
def search_teacher(search_value):
    teacher = mongo_t.db.teacher_profile.find_one({'profile.useridname_password.userid_name': search_value})
    if not teacher:
        teacher = mongo_t.db.teacher_profile.find_one({'profile.contact.email': search_value})
    if not teacher:
        teacher = mongo_t.db.teacher_profile.find_one({'profile.contact.phone': search_value})
    if teacher:
        teacher['_id'] = str(teacher['_id']) 
        data = {
            "_id": teacher['_id'],
            "role": teacher['role'],
            "user_id": teacher['profile']['useridname_password']['userid_name'],
            "username": teacher['username'],
            "user_image": teacher['user_image'],
        }
        return data
    return teacher


@app.route('/search_user/<invited_user_id>' , methods=['GET'])
def search_user(invited_user_id):
    invited_user_id = request.form.get("invited_user_id", '')   # searched and invited this will be added to selected_users list
    users = []
    student_profile = search_student(invited_user_id)
    parent_profile = search_parent(invited_user_id)
    teacher_profile = search_teacher(invited_user_id)

    # Determine the role of the invited user
    if student_profile:
        role = "student"
        users.append(student_profile)
    elif parent_profile:
        role = "parent"
        users.append(parent_profile)
    elif teacher_profile:
        role = "teacher"
        users.append(teacher_profile)
    else:
        return jsonify({"message": "User not found"}), 404
    
    return users, 200
accepted_users = {}

# Function to get details of friends
def get_friends_details(friends):
    details_list = []
    for friend in friends:
        student = search_student(friend)
        parent = search_parent(friend)
        teacher = search_teacher(friend)
        if student:
            data = mongo_s.db.student_profile.find_one({'user_id': friend})
        elif parent:
            data = mongo_p.db.parent_profile.find_one({'user_id': friend})
        elif teacher:
            data = mongo_t.db.teacher_profile.find_one({'user_id': friend})
        else:
            data = None

        if data:
            details = {
                "user_id": data['user_id'],
                "img": data['user_image'],
                "name": data['username'],
                "points": data['points']
            }
            details_list.append(details)

    return details_list

# Function to get friends of a user
def get_friends(user_id):
    data = mongo_s.db.student_profile.find_one({'user_id': user_id})
    friends = data.get("friends", [])
    return friends

# Function to send a notification
def send_notification(receiver, message):
    # print(f"Notification sent to {receiver['_id']}: {message}")
    print(f"Notification sent to {receiver}: {message}")

# Function to send a quiz invitation
def send_invitation(sender, invited_user, quiz_link):
    message = f"You have been invited to a quiz by {sender['username']} ({sender['user_id']}). Use this link to join the quiz: {quiz_link}"
    send_notification(invited_user, message)


def generate_room_code():
    # Generate a random 6-digit room code
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Function to generate a quiz_link with a combination of user_id and room_code[random]
def generate_quiz_link(user_id):
    try:
        # Generate a random 6-digit room code
        room_code = generate_room_code()
        # Here, you can generate the quiz link using user_id and room_code
        quiz_link = f'https://google.com/quiz/{user_id}/{room_code}'
        # quiz_link = f'quiz.com'
        return quiz_link, 200

    except Exception as e:
        response = {'error': str(e)}
        return jsonify(response), 500



# Define a route to invite friends and send quiz invitations
@app.route('/invite_friends_and_send_invitation/<user_id>/', methods=['GET', 'POST'])
def invite_friends_and_send_invitations(user_id):
    # Assuming you have a function search_student, search_parent, and search_teacher implemented elsewhere

    student_sending = search_student(user_id)
    parent_sending = search_parent(user_id)
    teacher_sending = search_teacher(user_id)

    # Check if the sender is present in student profile
    if student_sending:
        sender = mongo_s.db.student_profile.find_one({"user_id": user_id})
    elif parent_sending:
        sender = mongo_s.db.parent_profile.find_one({"user_id": user_id})
    elif teacher_sending:
        sender = mongo_t.db.teacher_profile.find_one({"user_id": user_id})
    else:
        return jsonify({"message": "Sender is not present in the database."}), 403

    friends = get_friends(user_id)
    friends_details = get_friends_details(friends)
    
    # selected_users = selected_users.split(',')
    selected_users = request.form.getlist('selected_users')    # here users which are selected from friends list will be added
    
    quiz_link = generate_quiz_link(user_id)

    for invited_friend_id in selected_users:
        send_invitation(sender, invited_friend_id, quiz_link)

    # Store the quiz link and selected users in the global variable
    accepted_users[quiz_link] = selected_users

    response_data = {
        "message": "Invitations sent successfully", 
        "quiz_link": quiz_link,
        "selected_users": selected_users,
        "friends_details": friends_details,
        "accepted_users": accepted_users[quiz_link]
    }

    return jsonify(response_data), 200

@app.route('/waiting_for_users/<quiz_link>', methods=['GET'])
def waiting_for_users(quiz_link):  # user_id and room_code
    # Retrieve the list of accepted users for the given quiz link
    if quiz_link in accepted_users:
        print(quiz_link)
        accepted_users_list = accepted_users[quiz_link]
        return jsonify({"accepted_users": accepted_users_list})
    else:
        return jsonify({"message": "Quiz link not found"}), 404


if __name__ == '__main__':
    app.run(debug=True)
