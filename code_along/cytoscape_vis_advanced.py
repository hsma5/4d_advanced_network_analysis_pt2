#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#######################################
### Step 1 - Python Library Imports ###
#######################################

import dash
import dash_html_components as html
import dash_core_components as dcc
import numpy as np
import pandas as pd
import dash_cytoscape as cyto
import networkx as nx
import matplotlib as mpl # see colorFader func.
from sklearn.preprocessing import StandardScaler # rescale numbers/ normalise data
from dash.dependencies import Input, Output # for callbacks

###################################################
### Step 2 - Persistent Local Variable Creation ###
###################################################

nodes_1 = pd.read_csv('../data/got-s1-nodes.csv', low_memory=False)
edges_1 = pd.read_csv('../data/got-s1-edges.csv', low_memory=False)

def create_nx_graph(nodeData,edgeData):
    """
    Helper function to create NetworkX Graph object based on 
    node and edge data provided.
    
    

    Parameters
    ----------
    nodeData : pd.DataFrame
        Node data i.e., id, label
    edgeData : pd.DataFrame
        Edge data ie., source, target, weight, etc

    Returns
    -------
    G : nx.Graph
        Network Graph object.

    """
    ## Initiate the graph object
    G = nx.Graph()
    
    ## Tranform the data into the correct format for use with NetworkX
    # Node tuples (ID, dict of attributes)
    idList = nodeData['Id'].tolist()
    labels =  pd.DataFrame(nodeData['Label'])
    labelDicts = labels.to_dict(orient='records')
    nodeTuples = [tuple(r) for r in zip(idList,labelDicts)]
    
    # Edge tuples (Source, Target, dict of attributes)
    sourceList = edgeData['Source'].tolist()
    targetList = edgeData['Target'].tolist()
    weights = pd.DataFrame(edgeData['Weight'])
    weightDicts = weights.to_dict(orient='records')
    edgeTuples = [tuple(r) for r in zip(sourceList,targetList,weightDicts)]
    
    # Add the nodes and edges to the graph
    # 'add_nodes_from' adds nodes from any iterable container
    G.add_nodes_from(nodeTuples)
    G.add_edges_from(edgeTuples)
    
    return G

def colorFader(c1,c2,mix=0): #fade (linear interpolate) from color c1 (at mix=0) to c2 (mix=1)
    """
    Creates a linear gradient colour fade between two colors 
        
    Parameters
    ----------
    c1 : str
        Colour value
    c2 : str
        Colour value
        
    mix : int (Default = 0)
        Value of 1 or 0

    Returns
    -------
    mpl.colors.to_hex((1-mix)*c1 + mix*c2) : str
        Hex colour value

    """
    
    c1=np.array(mpl.colors.to_rgb(c1))
    c2=np.array(mpl.colors.to_rgb(c2))
    return mpl.colors.to_hex((1-mix)*c1 + mix*c2)

def node_color_picker(par_df,col_name):
    """
    Function to work out the HEX value of the colour required for the node
    depending on where it sits on the gradient range from green to blue

    Parameters
    ----------
    par_df : pd.DataFrame
        Dataframe containing connectivity values.
    col_name : str
        Name of column containing values.

    Returns
    -------
    par_col_df : pd.DataFrame
        Dataframe containing gradient colour value

    """
    par_max = par_df.max()
    par_max = par_max.iloc[0]
    c1='#1f77b4' #blue
    c2='green' #green
    n=par_max
    
    par_col_list = list()
    for i in range(len(par_df)):
        par_val = par_df.iloc[i,0]
        color=colorFader(c1,c2,par_val/n)
        par_col_list.append(color)
    
    par_col_df = pd.DataFrame(par_col_list, columns=[col_name])
    
    return par_col_df

def create_analysis(G, nodes):
    """
    Function to assemble different NetworkX analysis so they they can 
    be used when creating the Cytoscape graph elements.
    #### CHECK THIS!

    Parameters
    ----------
    G : nx.Graph
        NetworkX Graph object
    nodes : pd.DataFrame
        Node list
        ###############################
        THIS DOESNT APPEAR TO BE USED?
        ###############################

    Returns
    -------
    full_an_df : TYPE
        Single dataframe containing all metrics.

    """
    # Node metrics
    # Diff measures of connectivity
    e_cent = nx.eigenvector_centrality(G)
    page_rank = nx.pagerank(G)
    degree = nx.degree(G)
    between = nx.betweenness_centrality(G)
    
    # Extract the analysis output and convert to a suitable scale and format
    e_cent_size = pd.DataFrame.from_dict(e_cent, orient='index',
                                         columns=['cent_value'])
    e_cent_size.reset_index(drop=True, inplace=True)
    #e_cent_size = e_cent_size*100
    page_rank_size = pd.DataFrame.from_dict(page_rank, orient='index',
                                            columns=['rank_value'])
    page_rank_size.reset_index(drop=True, inplace=True)
    #page_rank_size = page_rank_size*1000
    degree_list = list(degree)
    degree_dict = dict(degree_list)
    degree_size = pd.DataFrame.from_dict(degree_dict, orient='index',
                                         columns=['deg_value'])
    degree_size.reset_index(drop=True, inplace=True)
    between_size = pd.DataFrame.from_dict(between, orient='index',
                                          columns=['betw_value'])
    between_size.reset_index(drop=True, inplace=True)
    
    ### Uncomment to exagerate nodes attribute changes
    ### i.e. result is significantly different nodes
    # e_cent_size = e_cent_size*150
    # page_rank_size = page_rank_size*1000
    # degree_size = degree_size*2
    # between_size = between_size*1000
    
    dfs = [e_cent_size,page_rank_size,degree_size,between_size]
    df = pd.concat(dfs, axis=1)
    ## Uncomment to exagerate nodes attribute changes
    # an_df = df.copy(deep=True)
    # Comment out section up to the #### if exagerating node attribute changes
    df = pd.concat(dfs, axis=1)
    cols = list(df.columns)
    an_arr = df.to_numpy(copy=True)
    #### Scale data so each metric is comparable.
    scaler = StandardScaler()
    an_scaled = scaler.fit_transform(an_arr)
    an_df = pd.DataFrame(an_scaled)
    an_st = an_df.copy(deep=True)
    an_st.columns = cols
    an_df.columns = cols
    an_mins = list(an_df.min())
    #### As normalisation around zero - making everything into positive numbers
    for i in range(len(an_mins)):
        an_df[cols[i]] -= an_mins[i] - 1
        an_df[cols[i]] *= 12
    ####
    an_df.columns = ['cent_st_val', 'rank_st_val', 'deg_st_val', 'betw_st_val']
    col_names = ['e_cent_col', 'rank_col', 'deg_col', 'betw_col']
    for i in range(len(dfs)):
        ### colour the nodes....
        col_out = node_color_picker(dfs[i], col_names[i])
        ### re-creating 'df' now with the colours...
        df = pd.concat([df, col_out], axis=1)
    #### bringing together original and scaled versions of dataframes
    full_an_df = pd.concat([df, an_df], axis=1)
    
    return full_an_df

def create_cyto_graph(nodeData, edgeData, an_df):
    nodes_list = list()
    for i in range(len(nodeData)):
        node = {
                "data": {"id": nodeData.iloc[i,0], 
                         "label": nodeData.iloc[i,1],
                         "cent_val": an_df.iloc[i,8],
                         "cent_col": an_df.iloc[i,4],
                         "rank_val": an_df.iloc[i,9],
                         "rank_col": an_df.iloc[i,5],
                         "deg_val": an_df.iloc[i,10],
                         "deg_col": an_df.iloc[i,6],
                         "betw_val": an_df.iloc[i,11],
                         "betw_col": an_df.iloc[i,7]}
                
            }
        nodes_list.append(node)
    
    edges_list = list()
    for j in range(len(edges_1)):
        edge = {
                "data": {"source": edges_1.iloc[j,0], 
                         "target": edges_1.iloc[j,1],
                         "weight": edges_1.iloc[j,2]}
            }
        edges_list.append(edge)
    
    elements = nodes_list + edges_list
    return elements


G = create_nx_graph(nodes_1, edges_1)
full_an_df = create_analysis(G, nodes_1)
#### Extending the elements that need to go into the Cytoscape object
elements = create_cyto_graph(nodes_1, edges_1, full_an_df)

default_stylesheet=[
            {'selector': 'node',
                'style': {
                        'width': 'data(cent_val)', # these are now relative to the centrality value 
                        'height': 'data(cent_val)', # See Var Exp -> Elements -> Data (dict) -> cent_val
                        'background-color': 'data(cent_col)', # SEE HOW THESE ARE UPDATED IN CALLBACK FN change_metric
                        'content': 'data(label)',
                        'font-size': '40px',
                        'text-outline-color': 'white',
                        'text-outline-opacity': '1',
                        'text-outline-width': '8px',
                    }
                },
            {'selector': 'edge',
                'style': {
                        'line-color': 'grey'
                    }
                }
        ]

#####################################
### Step 3 - App. Initialisation ####
#####################################

app = dash.Dash(__name__)
server = app.server

############################
### Step 4 - App. Layout ###
############################

app.layout = html.Div(children=[
                cyto.Cytoscape(
                    id='cyto-graph',
                    className='net-obj',
                    elements=elements,
                    style={'width':'80%', 'height':'600px'},
                    layout={'name': 'cose',
                            'padding': 200,
                            'nodeRepulsion': '7000',
                            'gravityRange': '6.0',
                            'nestingFactor': '0.8',
                            'edgeElasticity': '50',
                            'idealEdgeLength': '200',
                            'nodeDimensionsIncludeLabels': 'true',
                            'numIter': '6000',
                            },
                    stylesheet=default_stylesheet
                    ),
                ### This drop down allows us to toggle between diff analysis
                ### i.e., eigen, PageRank, etc
                ### Setting this up ready for the callback below...
                dcc.Dropdown(
                    id='analysis-metric',
                    # List of dicts; keys: 'label' is human readable
                    # 'value' is a column name
                    options=[
                        {'label': 'Eigenvector centrality',
                         'value': 'cent_value'},
                        {'label': 'Page rank', 'value': 'rank_value'},
                        {'label': 'Degree', 'value': 'deg_value'},
                        {'label': 'Betweenness', 'value': 'betw_value'},
                        ],
                    clearable=False, # Always a value in drop down menu
                    multi=False,
                    value='cent_value', # inital data to display
                    style={'width': '200px'}
                    )
                ])

###################################
### Step 5 - App Callback Funcs ###
###################################

##### Here is were we use the input for the drop down.
##### to determine the styling on the graph which color and
#####  metric value we should be using. 
@app.callback(Output('cyto-graph', 'stylesheet'), # i.e., return from func below
          [Input('analysis-metric', 'value')]) # i.e., func below input
def change_metric(value):
    """
    User defined function required to change displayed metrics
    when dcc.Dropdown() is adjusted

    Parameters
    ----------
    value : TYPE
        DESCRIPTION.

    Returns
    -------
    default_stylesheet + new_styles : lists
        Lists of stylesheets

    """
    if value == 'cent_value':
        col = 'data(cent_col)'
        val = 'data(cent_val)'
    elif value == 'rank_value':
        col = 'data(rank_col)'
        val = 'data(rank_val)'
    elif value == 'deg_value':
        col = 'data(deg_col)'
        val = 'data(deg_val)'
    elif value == 'betw_value':
        col = 'data(betw_col)'
        val = 'data(betw_val)'
    
    #### below takes the same structure as default_stylesheet created previously
    #### List of dicts
    new_styles = [
        {
            'selector': 'node',
            'style': {
                'background-color': col,
                'width': val,
                'height': val,
                }
            }
        ]
    ### ??????? if default_stylesheet isn't a glbal variable- how can it be returned here?
    # i.e. we're just updating the selector:node bckg-colour, width & height.
    # will concat lists - as new_styles contains new, they will overwrite what's there...
    return default_stylesheet + new_styles

##################################
### Step 6 - App. Run Command ####
##################################

if __name__ == "__main__":
    app.run_server(debug=True)