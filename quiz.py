from flask import Flask, request, jsonify, request,render_template
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



if __name__ == '__main__':
    app.run(debug=True)