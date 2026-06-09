import plotly.graph_objects as go
import plotly.express as px
import networkx as nx

def generate_interactive_dag(workflow_steps):
    """
    Generates an interactive Plotly network graph representing the workflow DAG.
    """
    G = nx.DiGraph()
    
    # Define standard pipeline sequence
    categories = ["dataset", "preprocessing", "model", "evaluation", "explainability"]
    
    for i, step in enumerate(workflow_steps):
        G.add_node(step.name, category=step.category, reason=step.reason)
        if i > 0:
            G.add_edge(workflow_steps[i-1].name, step.name)
            
    # Position nodes sequentially along the x-axis
    pos = {step.name: (i, 0) for i, step in enumerate(workflow_steps)}
    
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='#475569'),
        hoverinfo='none',
        mode='lines'
    )
    
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    
    color_map = {
        "dataset": "#10b981", 
        "preprocessing": "#06b6d4", 
        "model": "#8b5cf6",
        "evaluation": "#ef4444",
        "explainability": "#ec4899"
    }
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        cat = G.nodes[node].get("category", "preprocessing")
        reason = G.nodes[node].get("reason", "")
        
        # Format hover text with HTML
        text = f"<b>{node}</b><br><i>{cat.upper()}</i><br><br>{reason}"
        node_text.append(text)
        node_color.append(color_map.get(cat, "#3b82f6"))
        
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[n for n in G.nodes()],
        textposition="bottom center",
        hoverinfo='text',
        hovertext=node_text,
        marker=dict(
            color=node_color,
            size=40,
            line_width=2,
            line_color='#E2E8F0'
        )
    )
    
    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=20,r=20,t=20),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                font=dict(color="#E2E8F0", family="Space Grotesk")
             ))
             
    # Add arrow annotations for directed edges
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        fig.add_annotation(
            x=(x0+x1)/2, y=(y0+y1)/2,
            ax=x0, ay=y0,
            xref='x', yref='y', axref='x', ayref='y',
            showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor='#475569'
        )
             
    return fig


def generate_experiment_comparison(experiments):
    """
    Generates a parallel coordinates plot or grouped bar chart to compare experiments.
    """
    if not experiments:
        return None
        
    exp_ids = [f"Exp {e['experiment_id'][:4]}" for e in experiments]
    scores = [e['score'] for e in experiments]
    models = [e['winner_model'] for e in experiments]
    
    fig = go.Figure(data=[
        go.Bar(
            name='Primary Metric',
            x=exp_ids,
            y=scores,
            text=[f"{s:.3f} ({m})" for s, m in zip(scores, models)],
            textposition='auto',
            marker_color='#06b6d4'
        )
    ])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#E2E8F0", family="Inter"),
        yaxis=dict(gridcolor='rgba(30,41,59,0.5)', title='Score'),
        xaxis=dict(title='Experiment'),
        margin=dict(l=0, r=0, t=30, b=0),
        height=350
    )
    
    return fig
