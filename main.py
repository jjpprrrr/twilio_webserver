from flask import Flask, request, redirect, session
import twilio.twiml

SECRET_KEY = 'lalalahacktech2017'
app = Flask(__name__)
app.config.from_object(__name__)

# Try adding your own number to this list!
callers = {
    "+13107487420": "Chenyang Zhong",
    "+14243828723": "Yifang Chen",
    "+1xxxxxxxxxx": "Ling Ye",
    "+1xxxxxxxxxx": "Yuelun Yang"
}

@app.route("/", methods=['GET', 'POST'])
def hello_monkey():
    """Respond to incoming texts with simple conversations."""

    counter = session.get('counter', 0)
    #counter += 1
    #session['counter'] = counter


    from_number = request.values.get('From', None)
    if from_number in callers:
        if counter == 0:
            message = 'Hey there, I know you are ' + callers[from_number] + '! '
            message += 'Are you going to Hacktech 2017? 1.yes; 2.no.'
            counter = 1 # 1 means received the top menu and heading over to the 2nd menu
        elif counter == 1:
            replied = request.values.get('Body', None).upper()
            if replied == '1' or replied == 'YES':
                message = 'You said YES! '
            elif replied == '2' or replied == 'NO':
                message = 'What a pity. '
            else:
                message = 'Sorry I do not understand. '
            counter = 0
        else:
            counter = 0
        # message += 'Now counter = ' + str(counter)
        session['counter'] = counter
    else:
        message = 'Oops wrong number. Counter = ' + str(counter)


    resp = twilio.twiml.Response()
    resp.message(message)
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
