import plotly.graph_objects as go
from datetime import timedelta

def make_notes_plot(df_notes) -> go.Figure:

    # Pandasデータフレームに変換
    df_pandas = df_notes.to_pandas()

    # Plotlyグラフの作成
    fig = go.Figure()
    
    # 最も新しい日付のインデックスと日付を取得
    latest_index = df_pandas['date'].idxmax()
    latest_date = df_pandas['date'].max()

    # 最新の日付から1週間前の日付までの範囲
    start_date = latest_date - timedelta(days=7)

    # 棒グラフ（notesの増加量）
    fig.add_trace(
        go.Bar(
            x=df_pandas['date'],
            y=df_pandas['increase'],
            name='Increase in Notes',
            yaxis='y2',
            opacity=0.75,
            marker_color=['orange' if i == latest_index else 'lightblue' for i in range(len(df_pandas))],
            text=[f"{v}" if i == latest_index else "" for i, v in enumerate(df_pandas['increase'])],  # 最新の日付のみ値を表示
            textposition="outside",  # テキストをバーの外側に表示
            textfont=dict(size=20),  # テキストを大きく表示
        )
    )

    # 折れ線グラフ（元のnotes）
    fig.add_trace(
        go.Scatter(
            x=df_pandas['date'],
            y=df_pandas['notes'],
            mode='lines+markers',
            name='Notes Count',
            yaxis='y1',
            text=[f"{v}" if i == latest_index else "" for i, v in enumerate(df_pandas['notes'])],  # 最新の日付のみ値を表示
        )
    )

    # グラフのタイトルとレイアウトの設定
    fig.update_layout(
        xaxis=dict(
            # title='Date',
            tickformat='%m-%d',  # 月単位で表示
            range=[start_date-timedelta(days=0.5), latest_date+timedelta(days=0.5)]  # 最新1週間にフォーカス
        ),
        yaxis=dict(
            title='Total Notes',
            side='left',
            range=[0, df_pandas['notes'].max()*1.1]
        ),
        yaxis2=dict(
            title='Notes by Day',
            side='right',
            overlaying='y',
            range=[0, df_pandas['increase'].max()*1.2]  # increaseの最大値をy軸の最大に設定
        ),
        legend=dict(xanchor='left',
                    yanchor='bottom',
                    x=0.02,
                    y=0.86,
                    orientation='v',
                    )
    )

    # グラフの返却
    return fig