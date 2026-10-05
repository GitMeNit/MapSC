import React, { useState, useEffect } from 'react';
import GraphView from './components/GraphView';
import Dashboard from './components/Dashboard';
import { Loader } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v1';

function App() {
  const [industry, setIndustry] = useState('ev-battery-minerals');
  const [elements, setElements] = useState([]);
  const [riskScores, setRiskScores] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [disruptedNode, setDisruptedNode] = useState<string | null>(null);
  const [simResult, setSimResult] = useState<any>(null);
  const [optResult, setOptResult] = useState<any>(null);

  useEffect(() => {
    fetchData();
  }, [industry]);

  const fetchData = async () => {
    setLoading(true);
    setDisruptedNode(null);
    setSimResult(null);
    setOptResult(null);
    try {
      const [graphRes, riskRes] = await Promise.all([
        fetch(`${API_BASE}/graph/${industry}/cytoscape`),
        fetch(`${API_BASE}/risk/${industry}/scores`)
      ]);
      const graphData = await graphRes.json();
      const riskData = await riskRes.json();
      
      setElements(graphData.elements);
      setRiskScores(riskData);
    } catch (err) {
      console.error("Failed to fetch data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulate = async (nodeId: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/simulation/${industry}/remove?target_node=${nodeId}`, { method: 'POST' });
      const data = await res.json();
      setSimResult(data);
      setDisruptedNode(nodeId);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = async (nodeId: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/optimizer/${industry}/run?chokepoint=${nodeId}&runs=3`);
      const data = await res.json();
      setOptResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', position: 'relative' }}>
      
      {/* Background Graph Layer */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 0 }}>
        {elements.length > 0 && (
          <GraphView elements={elements} onNodeClick={(id) => console.log("Clicked:", id)} disruptedNode={disruptedNode} />
        )}
      </div>

      {/* Overlay UI */}
      <div style={{ position: 'relative', zIndex: 10, display: 'flex', width: '100%', height: '100%', pointerEvents: 'none' }}>
        
        {/* Left Sidebar */}
        <div style={{ padding: '24px', pointerEvents: 'auto' }}>
          <Dashboard 
            industry={industry}
            riskScores={riskScores}
            onSimulate={handleSimulate}
            onOptimize={handleOptimize}
            loading={loading}
            simResult={simResult}
            optResult={optResult}
          />
        </div>
        
        {/* Loading Overlay */}
        {loading && (
          <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            <Loader size={48} color="#3b82f6" className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
            <div style={{ background: 'rgba(0,0,0,0.5)', padding: '4px 12px', borderRadius: '12px', fontSize: '14px' }}>Loading Data...</div>
            <style>
              {`@keyframes spin { 100% { transform: rotate(360deg); } }`}
            </style>
          </div>
        )}

        {/* Industry Selector (Top Right) */}
        <div style={{ position: 'absolute', top: '24px', right: '24px', pointerEvents: 'auto' }}>
          <select 
            className="glass-panel" 
            style={{ padding: '8px 16px', color: 'white', border: '1px solid rgba(255,255,255,0.2)', outline: 'none' }}
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
          >
            <option value="ev-battery-minerals">EV Battery Minerals</option>
            <option value="semiconductors">Semiconductors</option>
          </select>
        </div>

      </div>

    </div>
  );
}

export default App;
