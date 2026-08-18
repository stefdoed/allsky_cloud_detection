import matplotlib.pyplot as plt
import numpy as np

def render_heatmap_frac(data1_in, data2_in, txy, savename):

    # data1_in and data2_in are input arrays (same length)
    # mode: "frac" or "octa" --> octa only sets plot configs, data has to be converted manually
    # txy: array of shape (3): title, xlabel, ylabel
    # savename: save to path, set to -1 for no saving

        
    heatmap, xedges, yedges = np.histogram2d(data1_in, data2_in, bins=50, range=[[0,100],[0,100]])
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    
    plot_data = heatmap.T
    plot_data = np.log(plot_data)
    plot_data = np.where(np.isfinite(plot_data), plot_data, 0)
    
    plt.figure(figsize=(6,5), tight_layout=True)
    
    plt.imshow(plot_data, extent=extent, origin="lower", cmap="inferno")
    plt.colorbar(label="$log(N)$")
    plt.plot([0,100],[0,100], color="gray", linestyle="--")
    
    plt.ylim(0,100)
    plt.xlim(0,100)
    
    plt.title(txy[0])
    plt.xlabel(txy[1])
    plt.ylabel(txy[2])
    
    rmse = np.sqrt(1/len(data1_in)  *  np.nansum((data1_in - data2_in)**2))
    print("RMSE [%]:", rmse)

    if savename != -1:
        plt.savefig(savename)

def render_heatmap_octa(data1_in, data2_in, txy, savename):

    # data1_in and data2_in are input arrays (same length)
    # txy: array of shape (3): title, xlabel, ylabel
    # savename: save to path, set to -1 for no saving
    
    # expecting octa input

    heatmap, xedges, yedges = np.histogram2d(data1_in, data2_in, bins=9)
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    
    plot_data = heatmap.T
    plot_data = np.log(plot_data)
    plot_data = np.where(np.isfinite(plot_data), plot_data, 0)
    
    plt.figure(figsize=(6,5), tight_layout=True)
    
    plt.imshow(plot_data, origin="lower", cmap="inferno")
    plt.colorbar(label="$log(N)$")
    
    plt.title(txy[0])
    plt.xlabel(txy[1])
    plt.ylabel(txy[2])
    
    ax = plt.gca()
    for i in range(0,9):
        for j in range(0,9):
            ax.text(j,i,np.round(heatmap[j,i]/len(data1_in)*100,1), ha="center", va="center", color="white")
    
    rmse = np.sqrt(1/len(data1_in)  *  np.nansum((data1_in - data2_in)**2))
    print("RMSE [octa]:", rmse)

    if savename != -1:
        plt.savefig(savename)


def render_n_col(data_in, labels, title, savename):

    # data_in: array: len(data_in) must be number of input datasets n
    # labels: array of labels for plot, must be shape (n)
    # savename: save to path, set to -1 for no saving
    
    # expecting octa input
    
    n = len(data_in)
    col_width = 0.8 / n
    col_offsets = (np.arange(0, n) - (n-1)/2) * col_width
    
    hist_collector = []
    for i in range(0, n):
        hist_collector.append(np.histogram(data_in[i], bins=9, density=True))

    plt.figure(figsize=(6,5), tight_layout=True)

    for i in range(0, n):
        plt.bar(np.arange(0,9)+col_offsets[i], hist_collector[i][0], width=col_width, label=labels[i])

    plt.legend()
    plt.title(title)
    plt.xlabel("Octa")
    plt.ylabel("Probability Density")
    plt.xticks(range(0,9), range(0,9))

    if savename != -1:
        plt.savefig(savename)