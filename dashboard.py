import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from dashboard_utils import load_data, get_summary_stats

st.set_page_config(page_title="Patent Data Dashboard", layout="wide")
sns.set_theme(style="whitegrid")


@st.cache_data
def get_data():
    return load_data()


patents, inventors, companies, relationships, locations, all_years = get_data()
summary = get_summary_stats(patents, inventors, companies, relationships, locations)

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Data Preview"])
st.sidebar.markdown("---")
st.sidebar.info("Loaded first **500,000 rows** from each CSV for performance.")

if page == "Dashboard":
    st.title("Global Patent Intelligence Dashboard")
    st.markdown("Key analytics from the cleaned PatentsView dataset.")

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Patents", f"{summary['Total Patents']:,}")
    col2.metric("Inventors", f"{summary['Total Inventors']:,}")
    col3.metric("Companies", f"{summary['Total Companies']:,}")
    col4.metric("Relationships", f"{summary['Total Relationships']:,}")
    st.markdown("---")

    # Row 1: Trend + Recent Years
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Patent Volume Trend by Year")
        trend = all_years.dropna().groupby("year").size().reset_index(name="patent_count")
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.lineplot(data=trend, x="year", y="patent_count", marker="o", ax=ax)
        ax.set_xlabel("Year")
        ax.set_ylabel("Number of Patents")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        st.subheader("Top 15 Most Recent Years by Patent Count")
        recent = all_years["year"].value_counts().sort_index(ascending=False).head(15)
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.barplot(x=recent.values, y=recent.index.astype(str),
                    hue=recent.index.astype(str), palette="flare", legend=False, ax=ax)
        ax.set_xlabel("Number of Patents")
        ax.set_ylabel("Year")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    st.markdown("---")

    # Row 2: Top Companies + Top Inventors
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 15 Companies by Patent Count")
        top_companies = relationships.groupby("company_id").patent_id.nunique().reset_index()
        top_companies = top_companies.merge(
            companies[["company_id", "name"]].drop_duplicates(subset="company_id"),
            on="company_id", how="left"
        )
        top_companies = top_companies.rename(columns={"patent_id": "patent_count"})
        top_companies = top_companies.sort_values("patent_count", ascending=False).head(15)
        fig, ax = plt.subplots(figsize=(7, 6))
        sns.barplot(data=top_companies, x="patent_count", y="name",
                    hue="name", palette="mako", legend=False, ax=ax)
        ax.set_xlabel("Number of Patents")
        ax.set_ylabel("Company")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        st.subheader("Top 15 Inventors by Patent Count")
        top_inventors = relationships.groupby("inventor_id").patent_id.nunique().reset_index()
        top_inventors = top_inventors.merge(
            inventors[["inventor_id", "name"]].drop_duplicates(subset="inventor_id"),
            on="inventor_id", how="left"
        )
        top_inventors = top_inventors.rename(columns={"patent_id": "patent_count"})
        top_inventors = top_inventors.sort_values("patent_count", ascending=False).head(15)
        fig, ax = plt.subplots(figsize=(7, 6))
        sns.barplot(data=top_inventors, x="patent_count", y="name",
                    hue="name", palette="viridis", legend=False, ax=ax)
        ax.set_xlabel("Number of Patents")
        ax.set_ylabel("Inventor")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    st.markdown("---")

    # Row 3: Top Countries + Abstract Lengths
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 15 Countries by Patent Count")
        country_data = relationships.merge(
            inventors[["inventor_id", "country"]].drop_duplicates(subset="inventor_id"),
            on="inventor_id", how="left"
        )
        country_counts = (
            country_data.groupby("country").patent_id.nunique()
            .reset_index(name="patent_count")
            .sort_values("patent_count", ascending=False)
            .head(15)
        )
        fig, ax = plt.subplots(figsize=(7, 6))
        sns.barplot(data=country_counts, x="patent_count", y="country",
                    hue="country", palette="crest", legend=False, ax=ax)
        ax.set_xlabel("Number of Patents")
        ax.set_ylabel("Country")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        st.subheader("Distribution of Patent Abstract Lengths")
        abstracts = patents[["patent_id", "abstract"]].copy()
        abstracts["abstract_length"] = abstracts["abstract"].astype(str).str.len()
        sample_abs = abstracts["abstract_length"].sample(n=min(5000, len(abstracts)), random_state=42)
        fig, ax = plt.subplots(figsize=(7, 6))
        sns.histplot(sample_abs, bins=50, kde=True, color="skyblue", ax=ax)
        ax.set_xlabel("Abstract Length (characters)")
        ax.set_ylabel("Number of Patents")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

elif page == "Data Preview":
    st.header("Data Preview (First 5 Rows)")
    st.write("### Patents", patents.head())
    st.write("### Inventors", inventors.head())
    st.write("### Companies", companies.head())
    st.write("### Relationships", relationships.head())
    if locations is not None:
        st.write("### Locations", locations.head())
