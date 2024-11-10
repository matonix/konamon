import base64
import sqlite3
import polars as pl
import tempfile
import plotly.graph_objects as go
from notes import make_notes_plot
from dash import dcc, html

def get_score(contents):
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    with tempfile.NamedTemporaryFile(mode='wb') as temp_file:
        temp_file.write(decoded)  # ファイルの内容を書き込む
        temp_path = temp_file.name  # 一時ファイルのパスを取得

        # データベースに接続
        conn = sqlite3.connect(temp_path)

        df_player = pl.read_database(query="SELECT * FROM player", connection=conn)
        df_score = pl.read_database(query="SELECT * FROM score", connection=conn)
        
    date = pl.from_epoch(df_player["date"], time_unit='s')
    notes = df_player["epg"] + df_player["lpg"] + df_player["egr"] + df_player["lgr"] + df_player["egd"] + df_player["lgd"] + df_player["ebd"] + df_player["lbd"] + df_player["epr"] + df_player["lpr"] 
    df_notes = pl.DataFrame({
        "date": date[1:-1],
        "notes": notes[1:-1],
        "increase": (notes - notes.shift(1))[1:-1],
    })
    fig = make_notes_plot(df_notes).update_layout(margin=dict(l=10, r=10, t=10, b=10))
    return [
        html.Div([dcc.Graph(figure=fig)], style={'width': '25%', 'display': 'inline-block'}),
    ]
    

def get_scorelog(contents):
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    with tempfile.NamedTemporaryFile(mode='wb') as temp_file:
        temp_file.write(decoded)  # ファイルの内容を書き込む
        temp_path = temp_file.name  # 一時ファイルのパスを取得

        # データベースに接続
        conn = sqlite3.connect(temp_path)

        df_scorelog = pl.read_database(query="SELECT * FROM scorelog", connection=conn)
    
    df_song = pl.read_ipc("songdata.ipc")
    df_tag_filtered = pl.read_ipc("tags.ipc")
    
    df_song_tag = df_song.join(df_tag_filtered, on="md5", how="left")
    df_scorelog_song_tag = df_scorelog.join(df_song_tag, on="sha256", how="left")
    df_scorelog_song_tag
    date = pl.from_epoch(df_scorelog_song_tag["date"], time_unit='s')
    df_scorelog_song_tag_datetime = df_scorelog_song_tag.with_columns(date.alias("datetime"))
    df_scorelog_summary = df_scorelog_song_tag_datetime[["datetime", "title", "clear", "oldclear", "score", "oldscore", "combo", "oldcombo", "minbp", "oldminbp", "folder_name"]].filter(~pl.col("title").is_null())
    
    # 日付のみの列を作成
    df_scorelog_summary = df_scorelog_summary.with_columns(pl.col("datetime").dt.date().alias("date"))

    # 最新の日付を取得
    latest_date = df_scorelog_summary.select(pl.col("date").max()).item()

    # 最新の日付に一致する行を抽出
    df_today = df_scorelog_summary.filter(pl.col("date") == latest_date).unique()
    
    def bp_improve(x: dict) -> str:
        old: int = x["oldminbp"]
        new: int = x["minbp"]
        if old == 2147483647:
            return "new"
        else:
            return str(new - old)
    
    def clear_lamp(x: int) -> str:
        badges = [
            "NoPlay",
            "Failed",
            "AssistEasy",
            "LightAssistEasy",
            "Easy",
            "Normal",
            "Hard",
            "ExHard",
            "FullCombo",
            "Perfect",
            "Max",
        ]
        return badges[x]

    
    df_today_clear = df_today.filter(df_today["clear"] > df_today["oldclear"])
    tab_clear = go.Figure(data=[go.Table(
        header=dict(values=['Title', 'Folders', 'Clear']),
        cells=dict(
            values=[
                df_today_clear["title"], 
                df_today_clear["folder_name"], 
                df_today_clear["oldclear"].map_elements(clear_lamp, return_dtype=str) + "▶" + df_today_clear["clear"].map_elements(clear_lamp, return_dtype=str) 
                ],
            align='left'
            ),
        columnwidth=[9, 3, 5]
    )]).update_layout(margin=dict(l=10, r=10, t=10, b=10))
    
    df_today_score = df_today.filter(df_today["score"] > df_today["oldscore"])
    tab_score = go.Figure(data=[go.Table(
        header=dict(values=['Title', 'Folders', 'Score']),
        cells=dict(
            values=[
                df_today_score["title"], 
                df_today_score["folder_name"], 
                df_today_score["score"] + " (+" + (df_today_score["score"] - df_today_score["oldscore"]) + ")"
                ],
            align='left'
            ),
        columnwidth=[9, 3, 5]
    )]).update_layout(margin=dict(l=10, r=10, t=10, b=10))
    
    df_today_minbp = df_today.filter(df_today["minbp"] < df_today["oldminbp"])
    tab_minbp = go.Figure(data=[go.Table(
        header=dict(values=['Title', 'Folders', 'Min BP']),
        cells=dict(
            values=[
                df_today_minbp["title"], 
                df_today_minbp["folder_name"], 
                df_today_minbp["minbp"] + " (" + df_today_minbp.with_columns(pl.struct("oldminbp", "minbp").map_elements(bp_improve, return_dtype=str).alias("bp"))["bp"] + ")"
                ],
            align='left'
            ),
        columnwidth=[9, 3, 5]
    )]).update_layout(margin=dict(l=10, r=10, t=10, b=10))
    
    return [
        html.Div([dcc.Graph(figure=tab_clear)], style={'width': '25%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(figure=tab_score)], style={'width': '25%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(figure=tab_minbp)], style={'width': '25%', 'display': 'inline-block'}),
    ]
