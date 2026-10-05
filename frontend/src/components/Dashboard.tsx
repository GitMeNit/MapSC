import React from 'react';
import { AlertTriangle, Activity, Zap, RefreshCw } from 'lucide-react';

interface DashboardProps {
  industry: string;
  riskScores: any[];
  onSimulate: (nodeId: string) => void;
  onOptimize: (nodeId: string) => void;
  loading: boolean;
  simResult: any;
  optResult: any;
}

const Dashboard: React.FC<DashboardProps> = ({ 
  industry, 
  riskScores, 
  onSimulate, 
  onOptimize,
  loading,
  simResult,
  optResult
}) => {
  return (
    <div className="glass-panel" style={{ width: '400px', height: '100%', display: 'flex', flexDirection: 'column', padding: '20px', overflowY: 'auto' }}>
      
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={24} color="#3b82f6" />
          MapSC
        </h1>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>
          Industry: <span style={{ color: '#fff', fontWeight: 'bold' }}>{industry}</span>
        </div>
      </div>

      <div style={{ flex: 1 }}>
        <h2 style={{ fontSize: '16px', color: 'var(--text-muted)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={16} /> Top Risk Nodes
        </h2>
        
        {riskScores.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px 0' }}>No risk data available</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {riskScores.slice(0, 5).map((score, idx) => (
              <div key={idx} style={{ 
                background: 'rgba(255,255,255,0.05)', 
                borderRadius: '8px', 
                padding: '12px',
                borderLeft: `4px solid ${idx === 0 ? '#ef4444' : idx < 3 ? '#f59e0b' : '#3b82f6'}`
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <strong style={{ fontSize: '14px' }}>{score.Node_ID}</strong>
                  <span style={{ fontSize: '12px', background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: '4px' }}>
                    Risk: {score.Risk_Score.toFixed(2)}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn btn-danger" style={{ flex: 1, fontSize: '12px', padding: '6px' }} onClick={() => onSimulate(score.Node_ID)} disabled={loading}>
                    Simulate
                  </button>
                  <button className="btn" style={{ flex: 1, fontSize: '12px', padding: '6px' }} onClick={() => onOptimize(score.Node_ID)} disabled={loading}>
                    Optimize
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {simResult && (
          <div style={{ marginTop: '24px', padding: '16px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#ef4444' }}>Simulation Result</h3>
            <div style={{ fontSize: '13px' }}>
              <div><strong>Disrupted:</strong> {simResult.target_node}</div>
              <div><strong>Systemic Impact:</strong> {(simResult.systemic_impact_pct * 100).toFixed(1)}%</div>
              <div><strong>Downstream Nodes Affected:</strong> {simResult.downstream_nodes_affected}</div>
            </div>
          </div>
        )}

        {optResult && (
          <div style={{ marginTop: '24px', padding: '16px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#3b82f6' }}>Optimization Result</h3>
            <div style={{ fontSize: '13px' }}>
              <div><strong>Target:</strong> {optResult.chokepoint}</div>
              {Object.entries(optResult.algorithms).map(([algo, stats]: any) => (
                <div key={algo} style={{ marginTop: '8px' }}>
                  <strong>{algo.toUpperCase()}:</strong> {stats.improvement_vs_baseline_pct > 0 ? '+' : ''}{stats.improvement_vs_baseline_pct.toFixed(1)}% vs Baseline
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
    </div>
  );
};

export default Dashboard;
