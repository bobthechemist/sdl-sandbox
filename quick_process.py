# a hacked tool to do PCA on colorimetry data to see if it's possible.
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


import matplotlib.pyplot as plt

def splot(x, y, xlabel="x", ylabel="y", title="Scatter Plot", labels=None):
    """
    A simple scatter plot function for CHM414 students.

    Parameters
    ----------
    x : list or array
        Data for the x-axis
    y : list or array
        Data for the y-axis
    xlabel : str
        Label for the x-axis
    ylabel : str
        Label for the y-axis
    title : str
        Title for the plot
    labels : list or array (optional)
        Group labels for points (used for color coding)
    """

    plt.figure(figsize=(6, 5))

    if labels is None:
        plt.scatter(x, y, s=60, alpha=0.7, edgecolor='k')
    else:
        # Make points colored by labels
        unique_labels = list(set(labels))
        for lab in unique_labels:
            mask = [lbl == lab for lbl in labels]
            plt.scatter(
                [xi for xi, keep in zip(x, mask) if keep],
                [yi for yi, keep in zip(y, mask) if keep],
                s=60, alpha=0.7, edgecolor='k', label=str(lab)
            )
        plt.legend(title="Groups")

    plt.axhline(0, color='grey', lw=1)
    plt.axvline(0, color='grey', lw=1)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.title(title, fontsize=14)
    plt.grid(True, alpha=0.4)
    plt.tight_layout()
    plt.show()
    
    
df_all = pd.read_csv('scan_results.csv')
df = df_all.drop(['timestamp','x_position', 'y_position'],axis=1)
data = df.to_numpy()
data_scaled = StandardScaler().fit_transform(data)
cov_matrix = np.cov(data_scaled, rowvar=False, ddof=0)
print(cov_matrix.round(3))
vals, vecs = np.linalg.eig(cov_matrix)
sind = np.argsort(vals)[::-1]
vals = vals[sind]
vecs = vecs[sind]

print((vals/vals.sum()).round(3))
print(vecs.round(3))

loadings = vecs * np.sqrt(vals)

# For a better interpretation, let's put it in a data fram
loading_df = pd.DataFrame(
    loadings, # The values we are putting into the frame
    index=df.columns, # The names we will use for the rows comes from the original colums
    columns=[f'PC{i+1}' for i in range(len(df.columns))]) # Create as many PC1, PC2, ... as needed

print(f'\n==> Loadings:\n{loading_df}')
scores = data_scaled @ vecs

scores_df_3d = pd.DataFrame(
    scores[:, :3], 
    columns=['PC1', 'PC2', 'PC3']
)

scores_df_3d.to_csv('pca_scores_for_3d_plot.csv', index=False)

splot(scores[:,0], scores[:,1], xlabel="PC1", ylabel="PC2")
