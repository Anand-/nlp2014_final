
# coding: utf-8

# In[ ]:

from IPython.html.widgets import interact, interactive, fixed
from IPython.html import widgets
from IPython.display import clear_output, display, HTML
import matplotlib.pyplot as plt

def display_results(result):
    
    display(HTML("<h2>Keyphrase Overlaps<h2>"))
    plot_group_df(result['group_df'])
    
    groups=result['groups']
    text=[]
    for i, group in enumerate(groups):
        text.append("<div style='margin:2em'>")
        text.append("<h2>Group {}</h2>".format(i))
        text.append("<h>Keyphrases</h3>".format(i))
        text.append("<ul>")
        for k in group['keyphrases']:
            text.append("<li>{}</li>".format(k))
        text.append("</ul>")
        
        text.append("<h>Related URLs</h3>".format(i))
        text.append("<ul>")
        for k in group['urls']:
            text.append("<li><a href='{0}'>{0}</a></li>".format(k))        
        text.append("</ul>")
        
        text.append("</div>")
    
    display(HTML("".join(text)))
    
    


# In[1]:

def plot_group_df(group_df):
    plt.figure(figsize=(11,8))
    plt.pcolor(group_df.ix[:,2:], vmax=15)
    plt.gca().invert_yaxis()
    plt.colorbar()
    plt.show()

