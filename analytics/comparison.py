"""Helpers for selecting aligned feature pairs."""


def build_feature_pairs(df, feature_x, feature_y):
    if not {"date", feature_x, feature_y}.issubset(df.columns):
        raise ValueError("The selected features and date must exist in the DataFrame.")
    return df[["date", feature_x, feature_y]].dropna().sort_values("date").reset_index(drop=True)
