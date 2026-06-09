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
    "カシオペヤ座": (350, 25, 50, 75),
    "自由指定": (70, 95, -15, 15),
}

preset = st.selectbox("表示範囲", list(presets.keys()))
ra_min_default, ra_max_default, dec_min_default, dec_max_default = presets[preset]

# RA範囲
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

# Dec範囲
dec_range = st.slider(
    "赤緯 Dec [deg]",
    -90.0,
    90.0,
    (float(dec_min_default), float(dec_max_default)),
)

# 実視等級
vmag_limit = st.slider(
    "表示する実視等級",
    -2.0,
    7.0,
    3.5,
    0.5,
)

ra_min, ra_max = ra_range

# 赤経0度またぎに対応したフィルタ
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

# 表示用RAを作成
# 0度またぎの場合、350度台などを -10度台に変換して連続表示する
stars["plot_ra"] = stars["RAICRS"]

if crosses_zero:
    stars.loc[stars["plot_ra"] > 180, "plot_ra"] -= 360

# 点の大きさ
stars["size"] = ((7 - stars["Vmag"]) * 0.7).clip(lower=1)

fig = px.scatter(
    stars,
    x="plot_ra",
    y="DEICRS",
    size="size",
    hover_name="label",
    hover_data={
        "HIP": True,
        "RAICRS": ":.2f",
        "DEICRS": ":.2f",
        "Vmag": ":.2f",
        "pc": ":.1f",
        "Plx": ":.2f",
        "e_Plx": True,
        "B-V": True,
        "plot_ra": False,
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
