import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_daq as daq
import plotly.express as px
import pandas as pd
from PIL import Image
import base64
import io
import sqlite3
import polars as pl
import tempfile

from extractor import get_score, get_scorelog


app = dash.Dash(__name__)

app.layout = html.Div([
    # ファイルアップロード用エリア
    html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed',
                'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
            },
            multiple=True
        ),
        # データ表示用エリア
        html.Div(id='output-data-upload')
    ], style={'width': '100%', 'padding': '10px', 'boxSizing': 'border-box'}),

    # 画像アップロード用エリア
    html.Div([
        dcc.Upload(
            id='upload-image',
            children=html.Div(['Drag and Drop or ', html.A('Select Images')]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed',
                'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
            },
            multiple=True
        ),
        html.Div(id='output-image-upload', style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'})
    ], style={'width': '100%', 'padding': '10px', 'boxSizing': 'border-box'})
])

def parse_data(contents, filename):
    # ファイルの内容をDataFrameに変換
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return None
    except Exception as e:
        print(e)
        return None
    return df

@callback(Output('output-data-upload', 'children'),
          Input('upload-data', 'contents'),
          State('upload-data', 'filename'))
def update_output_data(list_of_contents, list_of_names):

    if list_of_contents is not None:
        children = []
        files = {filename: contents for contents, filename in zip(list_of_contents, list_of_names)}
    
        if "score.db" in list_of_names:
            contents = files["score.db"]
            score_divs = get_score(contents)
            children.extend(score_divs)
            
        if "scorelog.db" in list_of_names:
            contents = files["scorelog.db"]
            scorelog_divs = get_scorelog(contents)
            children.extend(scorelog_divs)
        
        return [html.Div(children)]
    return []

@callback(Output('output-image-upload', 'children'),
          Input('upload-image', 'contents'))
def update_output_image(list_of_images):
    if list_of_images is not None:
        images = []
        for image_data in list_of_images:
            content_type, content_string = image_data.split(',')
            decoded = base64.b64decode(content_string)
            img = Image.open(io.BytesIO(decoded))
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            # 幅を25%にして縦4分割し、画像が横に4枚並ぶように調整
            images.append(html.Div(
                html.Img(
                    src=f"data:image/png;base64,{img_base64}",
                    style={'width': '100%', 'height': 'auto'}
                ),
                style={'width': '25%', 'padding': '10px', 'boxSizing': 'border-box'}
            ))
        # 横に4枚並ぶようにFlexboxを設定
        return html.Div(images, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'flex-start'})
    return []

if __name__ == '__main__':
    app.run_server(debug=True)
