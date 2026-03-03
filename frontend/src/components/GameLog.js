import React from 'react';

function GameLog({ logs = [] }) {
  const logRef = React.useRef(null);

  React.useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="game-log" ref={logRef}>
      <h4>Game Log</h4>
      {logs.length === 0 ? (
        <div className="log-entry">Waiting for game to start...</div>
      ) : (
        logs.map((entry, i) => (
          <div key={i} className="log-entry">{entry}</div>
        ))
      )}
    </div>
  );
}

export default GameLog;
