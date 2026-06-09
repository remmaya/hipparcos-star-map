import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

CSV_FILE = "hipparcos_lite.csv"

st.title("Hipparcos Star Map / HR Diagram")

df = pd.read_csv(CSV_FILE)

for col in ["RAICRS", "DEICRS", "Vmag", "Plx", "e_Plx", "B-V"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["RAICRS", "DEICRS", "Vmag", "Plx"])
df = df[df["Plx"] > 0].copy()

df["pc"] = 1000 / df["Plx"]
df["AbsMag"] = df["Vmag"] + 5 - 5 * np.log10(df["pc"])

if "Name" not in df.columns:
    df["Name"] = ""

df["Name"] = df["Name"].fillna("").astype(str)
df["label"] = df["Name"]
df.loc[df["label"].str.strip() == "", "label"] = "HIP " + df["HIP"].astype(str)

mode = st.radio(
    "表示モード",
    ["星図", "HR図"],
    horizontal=True,
)

presets = {
    "オリオン座": (70, 95, -15, 15),
    "北斗七星": (160, 210, 45, 65),
    "カシオペヤ座": (0, 35, 50, 75),
    "南十字星": (180, 195, -65, -50),
    "さそり座": (230, 270, -50, 10),
    "はくちょう座": (280, 330, 20, 60),
    "夏の大三角": (270, 330, -10, 60),
    "冬の大三角": (70, 125, -20, 20),
    "プレアデス星団": (50, 65, 15, 35),
    "全天": (0, 360, -90, 90),
    "自由指定": (70, 95, -15, 15),
}

preset = st.selectbox("表示範囲", list(presets.keys()))
ra_min_default, ra_max_default, dec_min_default, dec_max_default = presets[preset]

show_names = st.checkbox("星名を表示", value=False)

if ra_min_default <= ra_max_default:
    ra_range = st.slider(
        "赤経 RA [deg]",
        0.0,
        360.0,
        (float(ra_min_default), float(ra_max_default)),
    )
else:
    st.write(f"赤経 RA [deg]：{ra_min_default}〜360, 0〜{ra_max_default}")
    ra_range = (float(ra_min_default), float(ra_max_default))

dec_range = st.slider(
    "赤緯 Dec [deg]",
    -90.0,
    90.0,
    (float(dec_min_default), float(dec_max_default)),
)

vmag_limit = st.slider(
    "表示する実視等級",
    -2.0,
    7.0,
    5.0,
    0.5,
)

ra_min, ra_max = ra_range

if ra_min <= ra_max:
    ra_filter = (df["RAICRS"] >= ra_min) & (df["RAICRS"] <= ra_max)
    crosses_zero = False
else:
    ra_filter = (df["RAICRS"] >= ra_min) | (df["RAICRS"] <= ra_max)
    crosses_zero = True

stars = df[
    ra_filter &
    (df["DEICRS"] >= dec_range[0]) &
    (df["DEICRS"] <= dec_range[1]) &
    (df["Vmag"] <= vmag_limit)
].copy()

stars["plot_ra"] = stars["RAICRS"]

if crosses_zero:
    stars.loc[stars["plot_ra"] > 180, "plot_ra"] -= 360

stars["size"] = ((7 - stars["Vmag"]) * 0.7).clip(lower=1)
stars["display_name"] = stars["Name"].fillna("").astype(str).str.strip()
stars.loc[stars["display_name"] == "", "display_name"] = ""

if mode == "星図":
    fig = px.scatter(
        stars,
        x="plot_ra",
        y="DEICRS",
        size="size",
        text="display_name" if show_names else None,
        hover_name="label",
        hover_data={
            "HIP": True,
            "RAICRS": ":.2f",
            "DEICRS": ":.2f",
            "Vmag": ":.2f",
            "AbsMag": ":.2f",
            "pc": ":.1f",
            "Plx": ":.2f",
            "e_Plx": True,
            "B-V": True,
            "plot_ra": False,
            "size": False,
            "display_name": False,
        },
    )

    bright = hr_stars[hr_stars["Vmag"] < 1.5]

    xaxis_title = "RA [deg]"
    if crosses_zero:
        xaxis_title = "RA [deg]（350°台は -10°台として表示）"

    fig.update_layout(
        title=f"{preset} 2D Star Map",
        xaxis_title=xaxis_title,
        yaxis_title="Dec [deg]",
        height=700,
    )

    if crosses_zero:
        x_min = ra_min - 360
        x_max = ra_max
    else:
        x_min = ra_min
        x_max = ra_max

    fig.update_xaxes(
        range=[x_max, x_min],
    )

    fig.update_yaxes(
        range=[dec_range[0], dec_range[1]],
        scaleanchor="x",
        scaleratio=1,
    )

    st.plotly_chart(fig, use_container_width=True)
    st.write(f"表示中の星数：{len(stars)}")

else:
    hr_stars = stars.dropna(subset=["B-V", "AbsMag"]).copy()

    fig = px.scatter(
        hr_stars,
        x="B-V",
        y="AbsMag",
        size="size",
        text="display_name" if show_names else None,
        hover_name="label",
        hover_data={
            "HIP": True,
            "Vmag": ":.2f",
            "AbsMag": ":.2f",
            "B-V": ":.2f",
            "pc": ":.1f",
            "Plx": ":.2f",
            "e_Plx": True,
            "RAICRS": ":.2f",
            "DEICRS": ":.2f",
            "size": False,
            "display_name": False,
        },
    )

    if show_names:
        fig.update_traces(
            textposition="top center",
            textfont=dict(size=12),
        )

    fig.update_layout(
        title=f"{preset} HR Diagram",
        xaxis_title="B-V 色指数",
        yaxis_title="絶対等級",
        height=700,
    )

    # HR図では明るい星ほど上に表示
    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(fig, use_container_width=True)
    st.write(f"表示中の星数：{len(hr_stars)}")
