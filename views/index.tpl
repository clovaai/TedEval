% import json
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>{{title}}</title>
        <meta charset="utf-8" />
        <link rel='stylesheet' href='{{ url('static', path='style.css') }}' />
        <script type="text/javascript" src="{{ url('static', path='jquery-1.8.2.min.js') }}" charset="utf-8"></script>
        <script type="text/javascript" src="{{ url('static', path='jquery.form-3.51.js') }}" charset="utf-8"></script>             
        <script type="text/javascript" src="{{ url('static', path='ranking.js') }}" charset="utf-8"></script>        
        <script type='text/javascript' src='https://www.google.com/jsapi'></script>
    </head>
    <body>
        
        <h1><a href="http://rrc.cvc.uab.es/" target="_blank"><img id='logo' src='/static/CVC.png'></a>{{title}}</h1>
        
        <div class='breadcrumbs'>
            Methods
            % if len(subm_data)>0:
                <button class='ml20 button-error pure-button' onclick="delete_methods()">Delete all methods</button> <span class="small">(You can also delete all methods by supressing all files from the output folder)</span>
            % end
            
            <a class="right" href="/exit">Exit</a>
        </div>
        
        <form action="/evaluate" method="post" enctype="multipart/form-data">
          Upload your method: 
          <label for='inp_title'>Title:</label><input type='text' name='title' maxlength="50" id='inp_title'>
          File:
          <input type="file" name="submissionFile" />
          % for k,v in submit_params.items():
                <label for='inp_{{k}}'>{{v['title']}}: </label>
                <select id='inp_{{k}}' name='{{k}}'>
                % for option in v['values']:
                    <option value='{{option['value']}}'>{{option['name']}}</option>
                % end
                </select>
          % end
          <button class="pure-button pure-button-primary" type="button" onclick="upload_subm()" >Evaluate</button>
        </form>
        <p class='info'>Dataset files of this Standalone: <a href='gt/images.zip'>Images</a> - <a href='gt/gt.{{extension}}'>Ground Truth</a> <button class="ml20 pure-button pure-button-secondary" type="button" onclick="instructions()" >See upload instructions..</button></p>
        <%
        if len(subm_data)>0:
            graphicRows = []
            graphic2Rows = []
        %>
        <table class='results ib'>
            <thead>
                <th>Method</th>
                <th>Submit date</th>
            <% 
             row = ["'Title'"]
             row2 = ["'Title'"]
             num_column = -1
             num_column_order = -1
             show2ndGraphic = False
             for k,v in method_params.items():
                num_column+=1
                if v['grafic'] == "1":
                    row.append("'" + v['long_name'] + "'")
                elif v['grafic'] == "2":
                    row2.append("'" + v['long_name'] + "'")
                end
                if v['order'] != "":
                    if v['grafic'] == "1":
                        num_column_order = num_column
                        sort_name = k
                        sort_name_long = v['long_name']
                        sort_order = v['order']
                        sort_format = v['format']
                        sort_type = v['type']
                    elif v['grafic'] == "2":
                        show2ndGraphic = True
                        sort2_name = k
                        sort2_name_long = v['long_name']
                        sort2_order = v['order']
                        sort2_format = v['format']
                        sort2_type = v['type']
                    end
                end            
            %>
                <th>{{v['long_name']}}</th>
            % end
            <th></th>
            % graphicRows.append("[" + ','.join(row) + "]")
            % graphic2Rows.append("[" + ','.join(row2) + "]")
            </thead>
            <tbody>
            
            <% 
                methodsData = []
                for id, title, date, methodResultJson in subm_data:
                    methodData = [id, title, date]
                    methodResult = json.loads(methodResultJson)
                    for k,v in method_params.items():
                        methodData.append(methodResult[k])
                    end
                    methodsData.append(methodData)
                end
                methodsData = sorted(methodsData, key=lambda methodData: methodData[2+num_column_order],reverse=sort_order=="desc")
            
                for methodData in methodsData:
                    id = methodData[0]
                    title = methodData[1]
                    date = methodData[2]
            %>
                <tr>
                    <td><a class='methodname' href='method/?m={{id}}'>{{id}}: <span class="title">{{title}}</span></a></td>
                <td><a href='method/?m={{id}}'>{{date}}</a></td>
                <% 
                row = ["'" + title.replace("'","\'") + "'"]
                row2 = ["'" + title.replace("'","\'") + "'"]
                index=0
                for k,v in method_params.items():
                    colValue = methodData[3+index]
                    if v['format'] == "perc" :
                        value = str(round(colValue*100,2)) + " %"
                        graphicValue = "{v:" + str(colValue) + ", f:'" + str(round(colValue*100,2)) + " %'}";
                    elif v['type'] == "double" :
                        value = str(round(colValue*100,2))
                        graphicValue =  "{v:" + str(colValue) + ", f:'" + str(round(colValue*100,2)) + "'}";
                    else:
                        value = colValue
                        graphicValue = colValue
                    end                    
                    if v['grafic'] == "1":
                        row.append(graphicValue)
                    elif v['grafic'] == "2":
                        row2.append(graphicValue)
                    end
                    %>
                    <td>{{value}}</td>
                    <% 
                    index += 1
                end %>
                <td><button class="mr5 pure-button" onclick="edit_method({{id}},this)">edit</button><button class="pure-button button-error"  onclick="delete_method({{id}})">x</button></td>
                % graphicRows.append("[" + ','.join(row) + "]")
                % graphic2Rows.append("[" + ','.join(row2) + "]")
                </tr>
            <% end
            graphicData = "[" + ','.join(graphicRows) + "]"
            base64Data = graphicData.encode('utf-8')
            graphic2Data = "[" + ','.join(graphic2Rows) + "]"
            base64Data2 = graphic2Data.encode('utf-8')
            
            %>
           </tbody>
        </table>
        
                    
        <input type="hidden" id='graphic' value='{{base64Data}}'>
        <input type="hidden" id='graphic-sort' value='{{sort_name_long}}'>
        <input type="hidden" id='graphic-type' value='{{sort_type}}'>
        <input type="hidden" id='graphic-format' value='{{sort_format}}'>
        
        <div id="div_rankings">
            <div id='div_ranking_1' style='overflow:hidden;display:inline-block;' class='ib'></div>

            % if show2ndGraphic:
                <input type="hidden" id='graphic-gr2' value='{{base64Data2}}'>
                <input type="hidden" id='graphic-gr2-sort' value='{{sort2_name_long}}'>
                <input type="hidden" id='graphic-gr2-type' value='{{sort2_type}}'>
                <input type="hidden" id='graphic-gr2-format' value='{{sort2_format}}'>        
                <div id='div_ranking_2' style='overflow:hidden;display:inline-block;' class='ib'></div>
            % end        
        </div>
        
        % else:
        <p class='info'>Upload your methods to see the method's ranking. </p>

        % end
        
        <div id='div_instructions' class='hidden'><div class='wrap'><button class='close pure-button button-error'>close</button><h1>Upload instructions</h1>
            <p class='info'>Note that the following instructions are for the Test Dataset, the example links may not work here if the dataset is not the Test Set.</p>
            {{ !instructions }}
        </div></div>
    </body>
</html>