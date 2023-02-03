import React, { useEffect, useState, useRef } from "react";
import useSwr from "swr";
import DeckGL from '@deck.gl/react';
import { TripsLayer } from '@deck.gl/geo-layers';
import { Map } from 'react-map-gl';
import { COORDINATE_SYSTEM } from '@deck.gl/core';

const INITIAL_VIEW_STATE = {
    longitude: -118.9815044403,
    latitude: 47.9610196694,
    zoom: 17,
    pitch: 45,
    bearing: 0,
}

const MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiaHVtYW5iZWFuanVpY2UiLCJhIjoiY2xkbmpranZwMGp6azNybzVseGt4Zjg2NSJ9.S2S--5ruauBWDkVphQQ7Dg";
const mapStyle = 'mapbox://styles/mapbox/light-v9';

const BLUE = [23, 184, 245];
const RED = [253, 128, 93];

const initialStyle = {
    position: 'relative',
    width: '100%',
    height: '60vh',
    border: '1px solid black'
}

const DeckMap = () => {


    const [species, setSpecies] = useState([]);
    const [selectedSpecies, setSelectedSpecies] = useState('Coho');
    const [intervalId, setIntervalId] = useState(null);
    const [time, setTime] = useState(0);
    const [fishStats, setFishStats] = useState('');

    const fetcher = (...args) => fetch(...args).then(response => response.json());
    const { data, error } = useSwr(`fish/${selectedSpecies}`, { fetcher });

    const mapData = data && !error ? data : [];




    // Get all unique fish species
    useEffect(() => {
        const fetchFishes = async () => {
            const response = await fetch('/fish/');
            const data = await response.json();
            setSpecies(data);
        };
        fetchFishes();
    }, [])

    // Get collection/release statistics for species
    useEffect(() => {
        const fetchStats = async () => {
            const response = await fetch(`stats/${selectedSpecies}`);
            const data = await response.json();
            setFishStats(data);
        };
        fetchStats();
    }, [selectedSpecies])

    // Set the seleted species
    const handleSelect = (event) => {
        const selection = event.target.value
        setSelectedSpecies(selection)
    }

    const timestamps = mapData.reduce(
        (ts, entry) => ts.concat(entry.timestamps),
        []
    );

    const layers = [
        new TripsLayer({
            coordinateSystem: COORDINATE_SYSTEM.METER_OFFSETS,
            coordinateOrigin: [-118.9815044403, 47.9610196694, 0],
            id: 'fish',
            data: mapData,
            getPath: d => d.path,
            getTimestamps: d => d.timestamps,
            getColor: d => (d.collected == 1.0 ? BLUE : RED),
            opacity: 0.8,
            widthMinPixels: 5,
            widthMaxPixels: 5,
            trailLength: 6,
            currentTime: time,
            billboard: true,
            jointRounded: true,
            positionFormat: 'XYZ',
            capRounded: true,
        })
    ];

    return (
        <div>
            <div key='dropdown'>
                <h1>Selected Species: {selectedSpecies}</h1>
                <select onChange={handleSelect} id='dropdownID'>
                    <option value="">Select Species</option>
                    {species.map(species => (
                        <option value={species}>{species}</option>
                    ))}
                </select>
            </div>
            <DeckGL
                controller={true}
                initialViewState={INITIAL_VIEW_STATE}
                layers={layers}
                style={initialStyle}
            >
                <Map mapboxAccessToken={MAPBOX_ACCESS_TOKEN} mapStyle={mapStyle}>
                </Map>
            </DeckGL>
            <div style={{ width: '100%', marginTop: "3.5rem" }}>
                <input
                    style={{ width: '100%' }}
                    type="range"
                    min="0"
                    max="1000"
                    step="0.00001"
                    value={time}
                    onChange={(e) => { setTime(Number(e.target.value)); }}
                />
            </div>
            <div className="legend">
                <svg height="50" width="200">
                    <circle
                        cx="20" cy="20" r="5" stroke="gray"
                        stroke-width="2" fill="rgb(253, 128, 93)"
                    />
                    <text x="30" y="25" fill="black"> = Not Collected</text>
                </svg>
                <svg height="50" width="200">
                    <circle
                        cx="20" cy="20" r="5" stroke="gray"
                        stroke-width="2" fill="rgb(23, 184, 245)"
                    />
                    <text x="30" y="25" fill="black"> = Collected</text>
                </svg>
            </div>
            <div>
                <table>
                    <th>
                        <tr>
                            <td>Total Number of {selectedSpecies} Released</td>
                            <td>Total Number of {selectedSpecies} Collected</td>
                            <td>Total {selectedSpecies} Collection Percentage</td>
                        </tr>
                        <tr>
                            <td>{fishStats.total_released}</td>
                            <td>{fishStats.total_collected}</td>
                            <td>{fishStats.total_percentage}</td>
                        </tr>
                    </th>
                    <tbody>

                    </tbody>
                </table>
            </div>
        </div>
    )

}

export default DeckMap;