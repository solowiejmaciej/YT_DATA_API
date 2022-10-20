from flask import Flask,jsonify
import sys
from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired

import processing

filePath='api/static/files/data.json'

app = Flask(__name__)

app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/files'

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("upload.")

def process():
    processing.process_data(filePath)
    processing.init()
    data = processing.process_videos()
    videos_by_channel = processing.process_channels()
    stats = processing.get_stats()
    return data,videos_by_channel,stats

test = NULL

@app.route('/')
@app.route('/how')
def how():
    return render_template('how.html')


@app.route('/upload_file', methods=['GET',"POST"])
def upload_file():
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data # First grab the file
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],'data.json')) # Then save the file
        data = process()
        processing.remover()
        return render_template('data.html', data=data)
    return render_template('upload_file.html', form=form)

@app.route('/about')
def about():
    return render_template('about.html')

    

if __name__ == '__main__':
    app.run(port=80,debug=False)