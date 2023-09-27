from flask import Flask, request, jsonify, request,render_template,redirect
from flask_pymongo import PyMongo
from bson import ObjectId
from bson import json_util
import json
# from pymongo.errors import DuplicateKeyError
# from werkzeug.utils import secure_filename
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
    print(all_entities)
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


# Quizz CRUD operations
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
            question_image_url = None

            if question_image and allowed_file(question_image.filename):
                try:
                    # filename = ''
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
                'options': options
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
        print("updaye",quiz)

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

# Get filtered quiz that show for exam as per student profile
@app.route('/get_filtered_quiz/<user_id>/<subject>/<topic>/<subtopic>/<level>', methods=['GET'])
def get_filtered_quiz(user_id, subject, topic, subtopic, level):
    try:
        All_quizz = get_filtered('quizes', mongo_q)
        student = get_student(user_id)
        filtered_data = []

        # Extract quiz IDs from the student's quiz_data
        student_quiz_ids = [quiz_data['quiz_id'] for quiz_data in student['quiz_data']]

        for quiz in All_quizz:
            quiz_id = quiz['_id']

            # Check if the quiz ID is not in the student's quiz_data
            if quiz_id not in student_quiz_ids:
                if (subject is None or quiz['subject'] == subject) and \
                (topic is None or quiz['topic'] == topic) and \
                (subtopic is None or quiz['subtopic'] == subtopic) and \
                (level is None or quiz['level'] == level):
                    filtered_data.append(quiz)

        # Check if any quizzes were found
        if not filtered_data:
            return jsonify({'message': "Quiz not found"}), 404

        return jsonify(filtered_data)

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


# setting status of quiz after click by user on quiz 
@app.route('/setting_status/<string:quiz_id>/<string:student_id>', methods = ['PUT'])
def setting_status_of_quizz(quiz_id, student_id):

    new_quiz = {
        "quiz_id": quiz_id,
        "status": "seen"
    }
    # Define the update operation to add the new quiz to the quiz_data array
    update = {
        '$push': {
            'quiz_data': {
                '$each': [new_quiz],
            }
        }
    }

    mongo_s.db.student_profile.update_one({'_id': student_id}, update)
    return "Quizz seen",200


#adding quizz in student profile
@app.route('/update_student_quiz_data/<string:quiz_id>/<string:student_id>/<string:result>/<string:click>', methods=['PUT'])
def update_student_quiz_data(quiz_id, student_id, result, click):
    try:
        student = mongo_s.db.student_profile.find_one({"_id": student_id})
        
        if student:
            # Check if the quiz_id already exists in quiz_data
            quiz_entry = next((entry for entry in student['quiz_data'] if entry.get('quiz_id') == quiz_id), None)

            if quiz_entry:
                quiz = mongo_q.db.quizes.find_one({"_id": quiz_id})
                # Update the existing quiz entry
                quiz_entry['subject'] = quiz.get('subject', '')
                quiz_entry['topic'] = quiz.get('topic', '')
                quiz_entry['class'] = quiz.get('class', '')
                quiz_entry['subtopic'] = quiz.get('subtopic', '')
                quiz_entry['language'] = quiz.get('language', '')            
                quiz_entry['result'] = result
                quiz_entry['clicked_on'] = click

                # Update the student's document with the modified quiz_data
                mongo_s.db.student_profile.update_one({"_id": student_id}, {"$set": student})

                return jsonify({"message": "Student quiz data updated successfully."}), 200
            else:
                return jsonify({"error": "Quiz not found in student data."}), 400
        else:
            return jsonify({"error": "Student not found."}), 400

    except Exception as e:
        return jsonify({"error": "An error occurred.", "error": str(e)}), 500


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

#serch parent by their unique identity
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

# Define a route to invite friends and send quiz invitations
@app.route('/invite_friends', methods=['POST'])
def invite_friends_and_send_invitations():
    user_id = request.form.get('user_id')  # user_id of sender who send invite
    student_sending = search_student(user_id)
    parent_sending = search_parent(user_id)
    teacher_sending = search_teacher(user_id)
    # Check if the sender is a present in student profile
    if student_sending:
        sender = mongo_s.db.student_profile.find_one({"_id": user_id})
    elif parent_sending:
        sender = mongo_s.db.parent_profile.find_one({"_id": user_id})
    elif teacher_sending:
        sender = mongo_s.db.teacher_profile.find_one({"_id": user_id})
    else:
        return jsonify({"message": "Sender is not a present in the database."}), 403

    friends = mongo_s.db.student_profile.find({"user_id": user_id, "friends": friends})
    selected_users = request.form.getlist('selected_users')
    invited_user_id = request.form.get("invited_user_id", '')
    # Search for the user by user_id in all three roles: student, parent, and teacher
    student_profile = search_student(invited_user_id)
    parent_profile = search_parent(invited_user_id)
    teacher_profile = search_teacher(invited_user_id)

    # Determine the role of the invited user
    if student_profile:
        role = "student"
        selected_users.append(student_profile)
    elif parent_profile:
        role = "parent"
        selected_users.append(parent_profile)
    elif teacher_profile:
        role = "teacher"
        selected_users.append(teacher_profile)
    else:
        jsonify({"message": "User not found"}), 404


    response_data = {
        "selected_users": selected_users
    }

    return jsonify(response_data), 200

@app.route('/send_invitation/<list:selected_users>', methods=['POST'])
def invite_friend(selected_users):
    # Get the user ID entered by the user   
    for user in selected_users:
        # Check if the invited user has the app installed (you may need to add this information to your user profiles)
        app_installed = user.get("app_installed", False)

        if app_installed:
            # Redirect to the quiz page
            return redirect("/quiz_page")
        else:
            # Redirect to the Play Store for app download
            return redirect("https://play.google.com/store/apps/details?id=your_app_package_name")


if __name__ == '__main__':
    app.run(debug=True)
