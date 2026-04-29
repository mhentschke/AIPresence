import React, { useState, useEffect } from 'react';
import { Backend } from '../Backend';
import styles from './EntityPicker.module.css';

const EntityPicker = ({ domain, value, onChange, label }) => {
  const [entities, setEntities] = useState(null);
  const [loading, setLoading] = useState(true);

  // Strip domain prefix for display (e.g. "device_tracker.sm_a720f" -> "sm_a720f")
  const prefix = domain ? domain + '.' : '';
  const shortValue = value && value.startsWith(prefix) ? value.slice(prefix.length) : value;

  const handleChange = (short) => {
    // Always pass full entity_id (domain.entity) to parent
    onChange(prefix + short);
  };

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Backend.GetHAEntities(domain)
      .then((result) => {
        if (!cancelled) {
          setEntities(result);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setEntities(null);
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, [domain]);

  if (loading) {
    return (
      <>
        {label && <label>{label}</label>}
        <div className={styles.wrapper}>
          <span className={styles.prefix}>{prefix}</span>
          <input className={styles.input} type="text" disabled placeholder="Loading entities..." />
        </div>
      </>
    );
  }

  if (entities === null) {
    return (
      <>
        {label && <label>{label}</label>}
        <div className={styles.wrapper}>
          <span className={styles.prefix}>{prefix}</span>
          <input
            className={styles.input}
            type="text"
            value={shortValue}
            onChange={(e) => handleChange(e.target.value)}
          />
        </div>
      </>
    );
  }

  const listId = `entity-list-${domain}`;
  return (
    <>
      {label && <label>{label}</label>}
      <div className={styles.wrapper}>
        <span className={styles.prefix}>{prefix}</span>
        <input
          className={styles.input}
          list={listId}
          type="text"
          value={shortValue}
          onChange={(e) => handleChange(e.target.value)}
        />
      </div>
      <datalist id={listId}>
        {entities.map((e) => {
          const short = e.entity_id.startsWith(prefix) ? e.entity_id.slice(prefix.length) : e.entity_id;
          return (
            <option key={e.entity_id} value={short}>
              {e.friendly_name}
            </option>
          );
        })}
      </datalist>
    </>
  );
};

export default EntityPicker;
