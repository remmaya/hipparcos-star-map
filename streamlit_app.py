import streamlit as st
import pandas as pd
import plotly.express as px

CSV_FILE = "hipparcos_lite.csv"

st.title("Hipparcos 2D Star Map")

df = pd.read_csv(CSV_FILE)

for col in ["RAICRS", "DEICRS", "Vmag", "Plx", "e_Plx", "B-V"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["RAICRS", "DEICRS", "Vmag", "Plx"])
df = df[df["Plx"] > 0].copy()

df["pc"] = 1000 / df["Plx"]

if "Name" not in df.columns:
    df["Name"] = ""

df["Name"] = df["Name"].fillna("").astype(str)
df["label"] = df["Name"]
df.loc[df["label"].str.strip() == "", "label"] = "HIP " + df["HIP"].astype(str)

presets = {
    "オリオン座": (70, 95, -15, 15),
    "北斗七星": (160, 210, 45, 65),
    "カシオペヤ座": (0, 25, 50, 75),
    "自由指定": (70, 95, -15, 15),
}

preset = st.selectbox("表示範囲", list(presets.keys()))

ra_min, ra_max, dec_min, dec_max = presets[preset]

ra_range = st.slider("赤経 RA [deg]", 0.0, 360.0, (float(ra_min), float(ra_max)))
dec_range = st.slider("赤緯 Dec [deg]", -90.0, 90.0, (float(dec_min), float(dec_max)))
vmag_limit = st.slider("表示する実視等級", -2.0, 7.0, 6.0, 0.5)

stars = df[
    (df["RAICRS"] >= ra_range[0]) &
    (df["RAICRS"] <= ra_range[1]) &
    (df["DEICRS"] >= dec_range[0]) &
    (df["DEICRS"] <= dec_range[1]) &
    (df["Vmag"] <= vmag_limit)
].copy()

stars["size"] = (8 - stars["Vmag"]).clip(lower=1)

fig = px.scatter(
    stars,
    x="RAICRS",
    y="DEICRS",
    size="size",
    hover_name="label",
    hover_data={
        "HIP": True,
        "Vmag": ":.2f",
        "pc": ":.1f",
        "Plx": ":.2f",
        "e_Plx": True,
        "B-V": True,
        "size": False,
    },
)

fig.update_layout(
    title=f"{preset} 2D Star Map",
    xaxis_title="RA [deg]",
    yaxis_title="Dec [deg]",
)

fig.update_xaxes(autorange="reversed")

st.plotly_chart(fig, use_container_width=True)

st.write(f"表示中の星数：{len(stars)}")
