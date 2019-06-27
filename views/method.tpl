<%
import json
import math
import web
%>
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>{{title}}</title>
        <meta charset="utf-8" />
        <link rel='stylesheet' href='{{ url('static', path='style.css') }}' />
    </head>
    <body>
        
        % submitId, methodTitle, submitDate, methodResultJson = subm_data
        
        <h1><a href="http://rrc.cvc.uab.es/" target="_blank"><img id='logo' src='/static/CVC.png'></a>{{title}}</h1>
        
        <div class='breadcrumbs'>
            <a href='/'>Methods</a> > {{methodTitle}}
        </div>        
        
        % result = json.loads(results.read('method.json'))
        % if result==None:
            <h2>Submit your method</h2>
        % elif result['calculated']==False:
            <h2>The method has not been calculated</h2>
            <p>{{result['Message']}}</p>
        % else:
            <div class="summary">
                <h2>Method summary</h2>
                <p>Title: <strong>{{methodTitle}}</strong> [{{submitId}}]</p>
                <p>Submit date: {{submitDate}}</p>
                <% for k,v in method_params.items():
                    colValue = result['method'][k]
                    if v['format'] == "perc" :
                        value = str(round(colValue*100,2)) + " %"
                    elif v['type'] == "double" :
                        value = str(round(colValue*100,2))
                    else:
                        value = colValue
                    end        
                %>
                    <p>{{v['long_name']}}: <strong>{{value}}</strong></p>
                % end
            </div>

            <div class='navigation'>
            %num_pages = int(math.ceil(float(len(images)) / 20))
            % if page>1:
                <a class="pure-button button-secondary" href='?m={{submitId}}&p={{page-1}}'>< previous</a>
            % end
            <span class='current'>Page {{page}} of {{num_pages}}</span>
            % if page<num_pages:
                <a class="pure-button button-secondary" href='?m={{submitId}}&p={{page+1}}'>next ></a>
            % end
            </div>
            
            <div class="samples_list">
            <%  
                for index, name in enumerate(images[(page-1)*20:page*20]):
                    sampleId = web.image_name_to_id(name)
                    values = json.loads(results.read( sampleId + '.json'))
                    sample = (page-1)*20+index+1
            %>
                    <div class='sample'>
                        <a href='/sample/?m={{submitId}}&sample={{str(sample)}}'><img src='/image_thumb/?c={{acronym}}&sample={{str(sample)}}' alt='{{name}}'></a>
                        <p><a href='/sample/?m={{submitId}}&sample={{str(sample)}}'>Sample: {{ str(sample)}}</a></p>
                        <p><a href='/sample/?m={{submitId}}&sample={{str(sample)}}'>ID: {{sampleId}}</a></p>
                        <% for k,v in sample_params.items():
                            colValue = values[k]
                            if v['format'] == "perc" :
                                value = str(round(colValue*100,2)) + " %"
                            elif v['type'] == "double" :
                                value = str(round(colValue*100,2))
                            else:
                                value = colValue
                            end        
                            %>
                            <p>{{v['long_name']}}: <strong>{{value}}</strong></p>
                        % end                        
                    </div>
            <%
                end
                results.close()
            %>
            </div>
        % end        
    </body>
</html>