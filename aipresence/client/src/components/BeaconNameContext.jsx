import React, { createContext, useState, useCallback, useContext, useEffect, useMemo } from 'react';
import { Backend } from '../Backend';

const BeaconNameContext = createContext({
  beaconNames: {},
  resolveBeaconName: () => ({ display: '', isNamed: false }),
  refreshBeaconNames: () => {},
});

export function useBeaconNames() {
  return useContext(BeaconNameContext);
}

export function BeaconNameProvider({ children }) {
  const [beaconNames, setBeaconNames] = useState({});

  const fetchBeaconNames = useCallback(async () => {
    try {
      const data = await Backend.GetBeaconNames();
      setBeaconNames(data);
    } catch (err) {
      console.error('Failed to fetch beacon names:', err);
    }
  }, []);

  useEffect(() => {
    fetchBeaconNames();
  }, [fetchBeaconNames]);

  const resolveBeaconName = useCallback((beaconId) => {
    if (!beaconId) return { display: '', isNamed: false };
    if (beaconNames[beaconId]) {
      return { display: beaconNames[beaconId], isNamed: true };
    }
    return { display: beaconId, isNamed: false };
  }, [beaconNames]);

  const contextValue = useMemo(
    () => ({ beaconNames, resolveBeaconName, refreshBeaconNames: fetchBeaconNames }),
    [beaconNames, resolveBeaconName, fetchBeaconNames]
  );

  return (
    <BeaconNameContext.Provider value={contextValue}>
      {children}
    </BeaconNameContext.Provider>
  );
}

export default BeaconNameContext;
