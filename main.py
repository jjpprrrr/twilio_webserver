import os
import io
from datetime import datetime
from datetime import timedelta
import tungsten
from flask import Flask, request, redirect, session, render_template
import twilio.twiml
from twilio.rest import TwilioRestClient

from google.cloud import datastore
from google.cloud import storage
from google.cloud import vision

import json
import urllib

CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET')

# for twilio
ACCOUNT_SID = 'ACb0e6ff909baa46d1b85b38f5e81991d1'
AUTH_TOKEN = '072780a0877c1c925da0e1ad8c582f65'

API_KEY = 'AIzaSyAWfdlsFQW2MnMBWavNZ20QGR99Oo0YHTQ'
T_API_KEY = 'XAR2QJ-Y93A7L7KY4'
SECRET_KEY = 'lalalahacktech2017'
app = Flask(__name__)
app.config.from_object(__name__)

callers = {
    "+13107487420": "Chenyang Zhong",
    "+14243828723": "Yifang Chen",
    "+16502789056": "Ling Ye",
    "+13235996623": "Yuelun Yang"
}

@app.route("/sms", methods=['GET', 'POST'])
def hello_monkey():
    """Respond to incoming texts with simple conversations."""

    from_number = request.values.get('From', None)
    if from_number in callers:
        from_person = callers[from_number]
    else:
        from_person = 'User'

    body = request.values.get('Body', None).lower()
    body_list = body.split(' ')
    body_list = body.split(' ')
    for i in range(len(body_list)):
        body_list[i] = body_list[i].lower()
    cmd = body_list[0]

    if cmd == 'hello' or cmd == 'hi':
        message = 'Hello ' + from_person + '! '
        message += 'For instructions, reply HELP.'
    elif cmd == 'help':
        message = """
        'list' will list out all items in the fridge. Use 'find <item>' to
        look for the number of a specific item. 'nutrition <item>' will provide
        you with detailed nutrition facts. 'expiration <item>' can automatically
        calculate which one is expiring and which one has expired. 'expiration <category>'
        would also work. 'recipe <item1> <item2> ...' will give you a link
        to useful recipes.
        """
    elif cmd == 'list':
        message = list_stock()
    elif len(body_list) <= 1:
        message = 'Sorry I have no idea what you are looking for.'
    else:
        if cmd == 'find':
            message = find_keyword(body_list[1])
        elif cmd == 'nutrition':
            message = get_nutrition(body_list[1])
        elif cmd == 'expiration':
            message = get_expiration(body_list[1])
        elif cmd == 'recipe':
            message = get_recipe(body_list[1:])
        else:
            message = 'sorry I do not understand'
#
    resp = twilio.twiml.Response()
    resp.message(message)
    return str(resp)

def list_stock():
    dc = datastore.Client()
    query = dc.query(kind='Items')
    item_entities = list(query.fetch())

    if len(item_entities) == 0:
        message = 'Nothing is in the fridge.'
    else:
        fruit_count = 0
        vege_count = 0
        product_count = 0
        beverage_count = 0
        # count number of items in each categories
        for item in item_entities:
            for keyword in item['keywords']:
                if keyword == 'fruit':
                    fruit_count += 1
                if keyword == 'vegetable':
                    vege_count += 1
                if keyword == 'product':
                    product_count += 1
                if keyword == 'beverage':
                    beverage_count += 1

        message = 'You have {0} fruit items, {1} vegetable items, {2} product items, and {3} beverage items.'.format(fruit_count, vege_count, product_count,beverage_count)

    return message

def find_keyword(keyword):
    dc = datastore.Client()
    query = dc.query(kind='Items')
    query.add_filter('keywords', '=', keyword)
    item_entities = list(query.fetch())

    if len(item_entities) == 0:
        message = 'No {0} item found in the fridge.'.format(keyword)
    else:
        message = '{0} {1} item found in the fridge.'.format(len(item_entities), keyword)

    return message

def get_nutrition(keyword):
    client = tungsten.Tungsten(T_API_KEY)
    result = client.query(keyword + ' food')
    cal = 'N/A'
    ch = 'N/A'
    fat = 'N/A'
    protein = 'N/A'

    for pod in result.pods:
        if pod.title == 'Calories':
            r = pod.format['plaintext'][0]
            l = r.split(' | ')
            for i in range(len(l)):
                if len(l[i])>=8:
                    if l[i][-8:] == 'calories':
                        cal = l[i+1]
                        break
        if pod.title == 'Carbohydrates':
            r = pod.format['plaintext'][0]
            l = r.split(' | ')
            for i in range(len(l)):
                if len(l[i])>=8:
                    if l[i][-13:] == 'carbohydrates':
                        ch = l[i+1]
                        break
        if pod.title == 'Fats and fatty acids':
            r = pod.format['plaintext'][0]
            l = r.split(' | ')
            for i in range(len(l)):
                if len(l[i])>=5:
                    if l[i][-3:] == 'fat':
                        fat = l[i+1]
                        break
        if pod.title == 'Protein and amino acids':
            r = pod.format['plaintext'][0]
            l = r.split(' | ')
            for i in range(len(l)):
                if len(l[i])>=5:
                    if l[i][-7:] == 'protein':
                        protein = l[i+1]
                        break
        if pod.title == 'Input interpretation':
            r = pod.format['plaintext'][0]
            amount = r.split(' | ')

    message = ''
    for a in amount:
        message += a
        message += ' '
    message += ','
    message += 'Calories: {0}; Carbohydrates: {1}; Fat: {2}; Protein: {3}'.format(cal, ch, fat, protein)
    return message

def get_expiration(keyword):

    # building a expiration date dictionary
    lifespan = {
        "apple": timedelta(days=28),
        "banana": timedelta(days=7),
        "orange": timedelta(days=21),
        "tomato": timedelta(days=10),
        "strawberry": timedelta(days=6),
        "butter": timedelta(days=180),
        "cream": timedelta(days=7),
        "egg": timedelta(days=21),
        "milk": timedelta(days=6),
        "yogurt": timedelta(days=10),
        "bread": timedelta(days=14),
        "broccoli": timedelta(days=10),
        "carrot": timedelta(days=28),
        "cucumber": timedelta(days=7),
        "garlic": timedelta(days=90),
        "onion": timedelta(days=28),
        "potato": timedelta(days=90),
        "pumpkin": timedelta(days=90)
    }

    message = ''

    dc = datastore.Client()
    query = dc.query(kind='Items')
    query.add_filter('keywords', '=', keyword)
    item_entities = list(query.fetch())


    if len(item_entities) == 0:
        message = 'Item not found in the fridge. '
    elif keyword in lifespan:
        t = lifespan[keyword]

        # create a dict of {days: numberOfItems}
        expiring = dict()
        expired = dict()

        for item in item_entities:
            d = item['timestamp'].replace(tzinfo=None) + t - datetime.now()
            if d.days >= 0:
                if d.days in expiring:
                    expiring[d.days] += 1
                else:
                    expiring[d.days] = 1
            else:
                if -1*d.days in expired:
                    expired[-1*d.days] += 1
                else:
                    expired[-1*d.days] = 1
        for key in expiring:
            message += '{0} {1} item will expire in {2} days. '.format(expiring[key], keyword, key)
        for key in expired:
            message += '{0} {1} item has expired for {2} days. '.format(expired[key], keyword, key)
    else:
        # create a dict of {days: numberOfItems}
        expiring = dict()
        expired = dict()

        for item in item_entities:
            found = False
            name = ''
            for k in item['keywords']:
                if k in lifespan:
                    found = True
                    name = k
                    break
            if found:
                t = lifespan[name]
                d = item['timestamp'].replace(tzinfo=None) + t - datetime.now()
                if d.days >= 0:
                    if d.days in expiring:
                        expiring[d.days] += 1
                    else:
                        expiring[d.days] = 1
                else:
                    if -1*d.days in expired:
                        expired[-1*d.days] += 1
                    else:
                        expired[-1*d.days] = 1
        for key in expiring:
            message += '{0} {1} item will expire in {2} days. '.format(expiring[key], keyword, key)
        for key in expired:
            message += '{0} {1} item has expired for {2} days. '.format(expired[key], keyword, key)

    return message

def get_recipe(keywords):
    message = 'https://www.google.com/search?q=' + keywords[0]
    if len(keywords) > 1:
        for i in range(1, len(keywords)):
            message += '+'
            message += keywords[i]
    return message

@app.route('/collect', methods=['POST'])
def collect_images():
    """collect incoming images sent by the camera."""
    photo = request.files['file']

    # Create a Cloud Storage client.
    storage_client = storage.Client()

    # Get the bucket that the file will be uploaded to.
    bucket = storage_client.get_bucket(CLOUD_STORAGE_BUCKET)

    # Create a new blob and upload the file's content.
    blob = bucket.blob(photo.filename)
    blob.upload_from_string(
            photo.read(), content_type=photo.content_type)

    # Make the blob publicly viewable.
    blob.make_public()

    # Create a Cloud Datastore client.
    datastore_client = datastore.Client()

    # Fetch the current date / time.
    current_datetime = datetime.now()

    # The kind for the new entity.
    kind = 'Images'

    # The name/ID for the new entity.
    name = blob.name

    # Create the Cloud Datastore key for the new entity.
    key = datastore_client.key(kind, name)

    entity = datastore.Entity(key)
    entity['blob_name'] = blob.name
    entity['image_public_url'] = blob.public_url
    entity['timestamp'] = current_datetime

    datastore_client.put(entity)

    # received_labels as a list of labels
    uri = 'gs://twilio-160408/' + blob.name
    received_labels = detect_labels_cloud_storage(uri)
    kind = 'Items'
    newkey = datastore_client.key(kind, name)
    ne = datastore.Entity(newkey)
    ne['keywords'] = received_labels
    ne['blob_name'] = blob.name
    ne['timestamp'] = current_datetime
    datastore_client.put(ne)
    inform_user(received_labels)

def inform_user(keywords):
    general = ['food', 'fruit', 'vegetable', 'product', 'beverage', 'drink']
    found = False
    for i in range(len(keywords)):
        if keywords[i] not in general:
            found = True
            name = keywords[i]
            break

    client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
    if found:
        client.messages.create(
            to='+13107487420',
            from_='+14243292970',
            body='New {0} item is added to the fridge.'.format(name)
        )
    else:
        client.messages.create(
            to='+13107487420',
            from_='+14243292970',
            body='New item is added to the fridge.'
        )


@app.route('/')
def homepage():
    datastore_client = datastore.Client()
    query = datastore_client.query(kind='Images')
    query.order = ['-timestamp']
    image_entities = list(query.fetch())

    q = datastore_client.query(kind='Items')
    q.order = ['-timestamp']
    keywords = list(q.fetch())
    return render_template('index.html', image_entities=image_entities, keywords=keywords, length=len(image_entities))

def detect_labels_cloud_storage(uri):
    """Detects labels in the file located in Google Cloud Storage."""
    theLabel = []
    vision_client = vision.Client()
    image = vision_client.image(source_uri=uri)
    # image = vision_client.image('storage.googleapis.com/twilio-160408/apple.jpg')
    labels = image.detect_labels()

    for label in labels:
        if knowledgeGraph(label.description):
            theLabel.append(label.description)

    return theLabel

def knowledgeGraph(query):
    service_url = 'https://kgsearch.googleapis.com/v1/entities:search'
    params = {
        'query': query,
        'limit': 15,
        'indent': True,
        'key': API_KEY,
    }
    url = service_url + '?' + urllib.urlencode(params)
    response = json.loads(urllib.urlopen(url).read())
    confidence = 0;
    #print('Knowledge: ')
    for element in response['itemListElement']:
        if 'description' in element['result']:
            temp = element['result']['description'].upper().split(' ')
            for i in temp:
                if i=='FOOD' or i=='BEVERAGE' or i=='DRINK' or i=='PRODUCT'  or i=='FRUIT' or i=='VEGETABLE' or i=="JUICE" or i=="SAUCE":
                    confidence+=1
            #print element['result']['description']
    if confidence>=3:
        return True
    else:
        return False

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
