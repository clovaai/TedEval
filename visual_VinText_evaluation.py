from flask import Flask,flash, render_template, Response, request, session, redirect, url_for, jsonify
from flask import send_from_directory ,send_file
from flask_restful import Resource, Api
from flask_cors import CORS

from flask_apscheduler import APScheduler


import urllib.parse
import requests

import os,io,sys,timeit
import zipfile,json,re,math
from datetime import datetime

# import web

sys.path.append('./')


import importlib
import sqlite3
import rrc_evaluation_funcs

from termcolor import colored
from config.config import *
evaluation_script = 'script_update'
from script_update import evaluate_method
from arg_parser import PARAMS

from PIL import Image


app = Flask(__name__)
app.secret_key = "secret key"
gTArchivePath = os.path.join(".","gt","gt.zip")
gTArchive = zipfile.ZipFile(gTArchivePath,'r')

def image_name_to_id(name):
    # m = re.match(image_name_to_id_str,name)
    # if m == None:
    #     return False
    # id = m.group(1)
    id = name.replace('.jpg', '').replace('.png', '').replace('.gif', '').replace('.bmp', '')
    if id+'.txt' not in gTArchive.namelist():
        return False
    return id


def get_sample_id_from_num(num):
    imagesFilePath = os.path.join(".","gt","images.zip")
    archive = zipfile.ZipFile(imagesFilePath,'r')
    current = 0
    for image in archive.namelist():
        if image_name_to_id(image) != False:
            current += 1
            if (current == num):
                return image_name_to_id(image)
            
    return False
	
def get_sample_from_num(num):
    imagesFilePath = os.path.join(".","gt","images.zip")
    archive = zipfile.ZipFile(imagesFilePath,'r')
    current = 0
    for image in archive.namelist():
        if image_name_to_id(image) != False:
            current += 1
            if (current == num):
                return image,archive.read(image)
            
    return False	

def get_samples():
    imagesFilePath = os.path.join(".","gt","images.zip")
    archive = zipfile.ZipFile(imagesFilePath,'r')
    num_samples = 0
    samples_list = []
    for image in archive.namelist():
        if image_name_to_id(image) != False:
            num_samples += 1
            samples_list.append(image)
    return num_samples,samples_list


@app.route('/delete_all', methods=['POST'])
def delete_all():
    output_folder = os.path.join(".", "output")
    try:    
        for root, dirs, files in os.walk(output_folder, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
    except:
        print("Unexpected error:", sys.exc_info()[0])


@app.route('/delete_method', methods=['POST'])
def delete_method():
    id = request.form['id']
    dbPath = os.path.join(".","output","submits")
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM submission WHERE id=?',(id))
    conn.commit()
    conn.close()
    
    try:
        output_folder = os.path.join(".","output","results_" + id)
        if os.path.isdir(output_folder):
            for root, dirs, files in os.walk(output_folder, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(output_folder)
        subm_file = os.path.join(".","output","results_" + id + "." + gt_ext)
        results_file = os.path.join(".","output","subm_" + id + ".zip")
        os.remove(subm_file)
        os.remove(results_file)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        

@app.route('/edit_method', methods=['POST'])
def edit_method():
    id = request.forms.get('id')
    name = request.forms.get('name')
    
    dbPath = os.path.join(".","output","submits")
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    cursor.execute('UPDATE submission SET title=? WHERE id=?',(name,id))
    conn.commit()
    conn.close()    
    
def get_all_submissions():
    dbPath = os.path.join(".","output","submits")
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS submission(id integer primary key autoincrement, title varchar(50), sumbit_date varchar(12),results TEXT)""")
    conn.commit()

    cursor.execute('SELECT id,title,sumbit_date,results FROM submission')
    sumbData = cursor.fetchall()
    conn.close()
    return sumbData


def get_submission(id):
    dbPath = os.path.join(".","output","submits")
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS submission(id integer primary key autoincrement, title varchar(50), sumbit_date varchar(12),results TEXT)""")
    conn.commit()
    
    cursor.execute('SELECT id,title,sumbit_date,results FROM submission WHERE id=?',(id,))
    sumbData = cursor.fetchone()
    conn.close()
    
    return sumbData


@app.route('/',methods=["GET","POST"])
def index():
    
    _,images_list = get_samples()

    page = 1
    if 'p' in request.args:
        page = int(request.args['p'])
        
    subm_data = get_all_submissions()
    subm_data = { id : [
        subm_data[id][0],
        subm_data[id][1],
        subm_data[id][2],
        subm_data[id][3]
        ]
        for id in range(len(subm_data))
    }
    vars = {
            'acronym':acronym, 
            'title':title,
            'images':images_list,
            'method_params':method_params,
            'page':page,
            'subm_data':subm_data,
            'sample_params':sample_params,
            'submit_params':submit_params,
            'instructions':instructions,
            'extension':gt_ext
            }
    return render_template('index.html',vars=vars)

@app.route('/test',methods=["GET","POST"])
def test():
    return jsonify({"name":"Thuyen"})

@app.route('/exit')
def exit():
    sys.stderr.close()




@app.route('/sample/')
def sample():
    
    num_samples,images_list = get_samples()    

    sample = int(request.args['sample'])
    methodId = request.args['m']
    subm_data = get_submission(methodId)

    samplesValues = []
    
    id = get_sample_id_from_num(int(sample))
    sampleId = id + ".json"
    
    subms = get_all_submissions()
    for methodId,methodTitle,_,_ in subms:
        sampleResults = {"id":methodId, "title":methodTitle}
        zipFolderPath = os.path.join(".","output","results_" + str(methodId))
        sampleFilePath = zipFolderPath + "/" + sampleId
        exist = True
        if os.path.isfile(sampleFilePath) == False:
            submFilePath = os.path.join(".","output","results_" + str(methodId) + ".zip")
            archive = zipfile.ZipFile(submFilePath,'r')
        
            if os.path.exists(zipFolderPath) == False:
                os.makedirs(zipFolderPath)
            try:
                archive.extract(sampleId, zipFolderPath)
            except:
                exist = False
        if exist:
            file = open(sampleFilePath,"r")
            results = json.loads(file.read())
            file.close()
        
        if exist:
            for k,v in sample_params.items():
                sampleResults[k] = results[k]
        else:
            for k,v in sample_params.items():
                sampleResults[k] = 0.0
        samplesValues.append( sampleResults )


    # for d in dir(request):
    #     print(d)
    vars = {
                'acronym':acronym,
                'title':title + ' - Sample ' + str(sample) + ' : ' + images_list[sample-1],
                'sample':sample,
                'num_samples':num_samples,
                'subm_data':subm_data,
                'samplesValues':samplesValues,
                'sample_params':sample_params,
                'customJS':customJS,
                'customCSS':customCSS
            }
    return render_template('sample.html',vars=vars)


@app.route('/evaluate', methods=['POST','GET'])
def evaluate():
    id=0
    submFile = request.files.get('submissionFile')
    if submFile is None:
        resDict = {"calculated":False,"Message":"No file selected"}
        if request.args['json']=="1":
            return json.dumps(resDict,indent=4)
        else:        
            vars = {
                # 'url':url, 
            'title':'Method Upload ' + title,'resDict':resDict}
            return render_template('upload.html',vars=vars)    
    else:
        
        name, ext = os.path.splitext(submFile.filename)
        if ext not in ('.' + gt_ext):
            resDict = {"calculated":False,"Message":"File not valid. A " + gt_ext.upper() + " file is required."}
            if request.args['json']=="1":
                return json.dumps(resDict,indent=4)            
            else:
                vars = {
                    # 'url':url, 
                    'title':'Method Upload ' + title,'resDict':resDict}
                return render_template('upload.html',vars=vars)    
    
        p = {
            'g': os.path.join(".","gt","gt." + gt_ext), 
            's': os.path.join(".","output","subm." + gt_ext), 
            'o': os.path.join(".","output")
        }
        global PARAMS
        setattr(PARAMS, 'GT_PATH', os.path.join(".","gt","gt." + gt_ext))
        setattr(PARAMS, 'SUBMIT_PATH', os.path.join(".","output","subm." + gt_ext))
        setattr(PARAMS, 'OUTPUT_PATH', os.path.join(".","output"))

        # apply response to evaluation
        if 'transcription' in request.form.keys() and request.form['transcription'] == 'on':
            setattr(PARAMS, 'TRANSCRIPTION', True)
        else:
            setattr(PARAMS, 'TRANSCRIPTION', False)
        
        if 'confidence' in request.form.keys() and request.form['confidence'] == 'on':
            setattr(PARAMS, 'CONFIDENCES', True)
        else:
            setattr(PARAMS, 'CONFIDENCES', False)

        if 'mode' in request.form.keys() and request.form['mode'] == 'endtoend':
            setattr(PARAMS, 'E2E', True)
        else:
            setattr(PARAMS, 'E2E', False)
        for k,_ in submit_params.items():
            p['p'][k] = request.form.get(k)

        if os.path.isfile(p['s']):
            os.remove(p['s'])

        submFile.save(p['s'])

        module = importlib.import_module(evaluation_script )
        resDict = rrc_evaluation_funcs.main_evaluation(p,module.default_evaluation_params,module.validate_data,evaluate_method)

        
        if resDict['calculated']==True:
            dbPath = os.path.join(".","output","submits")
            conn = sqlite3.connect(dbPath)
            cursor = conn.cursor()
            
            if 'title' in request.form.keys():
                submTitle = request.form['title']
            if submTitle=="":
                submTitle = "unnamed"
                
            cursor.execute('INSERT INTO submission(title,sumbit_date,results) VALUES(?,?,?)',(submTitle ,datetime.now().strftime("%Y-%m-%d %H:%M"),json.dumps(resDict['method'],indent=4)))
            conn.commit()
            id = cursor.lastrowid

            os.rename(p['s'], p['s'].replace("subm." + gt_ext,"subm_" + str(id) + "." + gt_ext) )
            os.rename(p['o'] + "/results.zip", p['o'] + "/results_" + str(id) + ".zip" )

            conn.close()

        # if request.args['json']=="1":
        #     return json.dumps( {"calculated": resDict['calculated'],"Message": resDict['Message'],'id':id},indent=4 )
        # else:
        vars = {
            # 'url':url, 
        'title':'Method Upload ' + title,'resDict':resDict,'id':id}
        return render_template('upload.html',vars=vars)    

@app.route('/image_thumb/', methods=['GET'])
def image_thumb():

    sample = int(request.args['sample'])
    fileName,data = get_sample_from_num(sample)
    ext = fileName.split('.')[-1]
    
    f = io.BytesIO(data)	
    image = Image.open(f)

    maxsize = (205, 130)
    image.thumbnail(maxsize)
    output = io.BytesIO()
	
    if ext=="jpg":
            im_format = "JPEG"
            header = "image/jpeg"
            image.save(output,im_format, quality=80, optimize=True, progressive=True)
    elif ext == "gif":
            im_format = "GIF"
            header = "image/gif"
            image.save(output,im_format)
    elif ext == "png":
            im_format = "PNG"
            header = "image/png"
            image.save(output,im_format, optimize=True)
    
    contents = output.getvalue()

    output.close()
    
    return send_file(
        io.BytesIO(contents),
        mimetype='image/jpeg',
        )

@app.route('/image/', methods=['GET'])
def image():
    sample = int(request.args['sample'])
    fileName,data = get_sample_from_num(sample)

    ext = fileName.split('.')[-1]
    f = io.BytesIO(data)
    image = Image.open(f)
    output = io.BytesIO()
    if ext=="jpg":
            im_format = "JPEG"
            header = "image/jpeg"
            image.save(output,im_format, quality=80, optimize=True, progressive=True)
    elif ext == "gif":
            im_format = "GIF"
            header = "image/gif"
            image.save(output,im_format)
    elif ext == "png":
            im_format = "PNG"
            header = "image/png"
            image.save(output,im_format, optimize=True)        
    
    
    contents = output.getvalue()
    output.close()
    
    body = data

    return send_file(
        io.BytesIO(contents),
        mimetype='image/jpeg',
        )

@app.route('/gt/<path:path>')
def send_gt(path):
    return send_from_directory('gt', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route('/sampleInfo/', methods=['GET'])
def get_sample_info():
    methodId = request.args['m']    
    print(methodId)
    submFilePath = os.path.join(".","output","results_" + str(methodId) + ".zip")
    archive = zipfile.ZipFile(submFilePath,'r')
    id = get_sample_id_from_num(int(request.args['sample']))
    results = json.loads(archive.read(id + ".json"))
    return json.dumps(results)

@app.route('/method/', methods=['GET'])
def method():
    # print(dir(request))
    # print(request.full_path)
    print(request.host_url)
    # input()
    _,images_list = get_samples()
    
    results = None
    page = 1
    subm_data = {}
    if 'm' in request.args:
        id = request.args['m']
        submFilePath = os.path.join(".","output","results_" + id   + ".zip")

        if os.path.isfile(submFilePath):
            results = zipfile.ZipFile(submFilePath,'r')
        if 'p' in request.args:
            page = int(request.args['p'])
        
        subm_data = get_submission(id)
        print("subm_data",subm_data)
        if results is None or subm_data is None:
            redirect('/')
    else:
        redirect('/')
    if subm_data is None:
        redirect('/')
    # submitId, methodTitle, submitDate, methodResultJson = subm_data

    subm_data = {
        "submitId":subm_data[0],
        "methodTitle":subm_data[1],
        "submitDate":subm_data[2],
        "methodResultJson":subm_data[3]
    }
    vars = {
        'id':id,
        'acronym':acronym, 
        'title':title,
        'images':images_list,
        'method_params':method_params,
        'sample_params':sample_params,
        'results':results,
        'page':page,
        'subm_data':subm_data
    }
    return render_template('method.html',vars=vars)


if __name__=='__main__':
    scheduler = APScheduler()

    def sorted_samplesData(samplesData,num_column_order,sort_order):
        return sorted(samplesData, key=lambda sample:
                    sample[num_column_order],reverse=sort_order=="desc" ) 
    def custom_json_filter(zip_path,sampleId):
        print(zip_path,sampleId)
        try:
            return json.loads(zipfile.ZipFile(zip_path).read( sampleId + '.json'))
        except Exception as ex:
            print(ex)
            return {'recall':0,'precision':0,'hmean':0}    
    app.jinja_env.globals.update(zipfile=zipfile.ZipFile)
    app.jinja_env.globals.update(json=json)
    app.jinja_env.globals.update(round=round)
    app.jinja_env.globals.update(math=math)
    app.jinja_env.globals.update(image_name_to_id=image_name_to_id)
    app.jinja_env.globals.update(enumerate=enumerate)
    app.jinja_env.globals.update(sorted_samplesData=sorted_samplesData)
    app.jinja_env.globals.update(custom_json_filter=custom_json_filter)

    host = '127.0.0.1'
    port = 8081
    scheduler.init_app(app)
    scheduler.start()
    app.run(host=host, port=port, debug=True)
    
    
    
