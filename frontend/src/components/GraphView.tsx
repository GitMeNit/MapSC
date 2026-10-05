import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

interface GraphViewProps {
  elements: any[];
  onNodeClick: (nodeId: str) => void;
  disruptedNode?: string | null;
}

const GraphView: React.FC<GraphViewProps> = ({ elements, onNodeClick, disruptedNode }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current || elements.length === 0) return;

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'background-color': '#3b82f6',
            'color': '#fff',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '10px',
            'width': '60px',
            'height': '60px',
            'text-outline-color': '#0f172a',
            'text-outline-width': 1.5,
          }
        },
        {
          selector: 'node[type="Company"]',
          style: { 'background-color': '#8b5cf6', 'shape': 'round-rectangle' }
        },
        {
          selector: 'node[type="Material"]',
          style: { 'background-color': '#10b981', 'shape': 'hexagon' }
        },
        {
          selector: 'node[type="Country"]',
          style: { 'background-color': '#f59e0b', 'shape': 'ellipse' }
        },
        {
          selector: 'node[type="Facility"]',
          style: { 'background-color': '#ef4444', 'shape': 'triangle' }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': 'rgba(255,255,255,0.2)',
            'target-arrow-color': 'rgba(255,255,255,0.2)',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '8px',
            'color': '#94a3b8',
            'text-rotation': 'autorotate',
            'text-margin-y': -10
          }
        },
        {
          selector: '.disrupted',
          style: {
            'background-color': '#ef4444',
            'border-width': 4,
            'border-color': '#fff',
            'width': '70px',
            'height': '70px'
          }
        },
        {
          selector: '.affected',
          style: {
            'opacity': 0.3
          }
        }
      ],
      layout: {
        name: 'cose',
        padding: 50,
        nodeRepulsion: () => 4000,
        idealEdgeLength: () => 100,
        edgeElasticity: () => 100,
      }
    });

    cy.on('tap', 'node', (evt) => {
      onNodeClick(evt.target.id());
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [elements, onNodeClick]);

  useEffect(() => {
    if (cyRef.current && disruptedNode) {
      cyRef.current.elements().removeClass('disrupted affected');
      const root = cyRef.current.getElementById(disruptedNode);
      if (root) {
        root.addClass('disrupted');
        // Simple mock visual propagation
        root.successors().addClass('affected');
      }
    } else if (cyRef.current && !disruptedNode) {
      cyRef.current.elements().removeClass('disrupted affected');
    }
  }, [disruptedNode]);

  return (
    <div 
      ref={containerRef} 
      style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }} 
    />
  );
};

export default GraphView;
