'use client';
import React, { useRef, useMemo, useState, useEffect, useCallback } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Line } from '@react-three/drei';
import * as THREE from 'three';

// Node component with bouncy animation
function Node({ position, id, isHighlighted, isTarget, isClicked, onHover, onLeave, onClick }: {
  position: [number, number, number];
  id: number;
  isHighlighted: boolean;
  isTarget: boolean;
  isClicked: boolean;
  onHover: () => void;
  onLeave: () => void;
  onClick: () => void;
}) {
  const glowRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (glowRef.current) {
      const scale = hovered ? 1.5 : (isHighlighted ? 1.3 : 1.0);
      
      glowRef.current.position.y = position[1];
      glowRef.current.position.z = position[2] + 0.1; // Slightly above edges
      glowRef.current.scale.setScalar(scale);
      
      if (isClicked) {
        glowRef.current.material.opacity = 1.0;
        glowRef.current.material.color.setHSL(0.15, 0.9, 0.8); // Yellow
      } else if (isHighlighted || isTarget) {
        glowRef.current.material.opacity = 1.0;
        glowRef.current.material.color.setHSL(0.15, 0.9, 0.8);
      } else {
        glowRef.current.material.opacity = 1.0;
        glowRef.current.material.color.setHSL(0, 0, 0); // Solid black
      }
    }
  });

  return (
    <group>
      <mesh
        ref={glowRef}
        position={position}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
          onHover();
        }}
        onPointerOut={(e) => {
          e.stopPropagation();
          setHovered(false);
          onLeave();
        }}
        onClick={(e) => {
          e.stopPropagation();
          onClick();
        }}
      >
        <circleGeometry args={[0.4, 32]} />
        <meshBasicMaterial
          color={isClicked ? "#FFD700" : isTarget ? "#FFD700" : isHighlighted ? "#FFA500" : "#000000"}
          transparent={false}
        />
      </mesh>
    </group>
  );
}

// Edge component with flowing animation
function Edge({ start, end, isActive, isPath }: {
  start: [number, number, number];
  end: [number, number, number];
  isActive: boolean;
  isPath: boolean;
}) {
  const lineRef = useRef<THREE.Line>(null);
  const glowRef = useRef<THREE.Line>(null);
  const points = useMemo(() => [
    new THREE.Vector3(start[0], start[1], 0), // Edges at z=0
    new THREE.Vector3(end[0], end[1], 0)
  ], [start, end]);

  useFrame((state) => {
    if (lineRef.current) {
      const time = state.clock.getElapsedTime();
      
      if (isPath) {
        lineRef.current.material.opacity = 0.8;
        lineRef.current.material.color.setHSL(0.15, 0.9, 0.8);
      } else if (isActive) {
        lineRef.current.material.opacity = 0.85;
        lineRef.current.material.color.setHSL(0.15, 0.8, 0.8);
      } else {
        lineRef.current.material.opacity = 0.8;
        lineRef.current.material.color.setHSL(0, 0, 0.3); // Darker gray
      }
    }

    if (glowRef.current) {
      if (isPath || isActive) {
        glowRef.current.material.opacity = 0.5;
      } else {
        glowRef.current.material.opacity = 0;
      }
    }
  });

  return (
    <group>
      <Line
        ref={glowRef}
        points={points}
        color={isPath ? "#FFD700" : "#FFA500"}
        lineWidth={isPath ? 6 : 3}
        transparent
        opacity={0.1}
      />
      
      <Line
        ref={lineRef}
        points={points}
        color={isPath ? "#FFD700" : isActive ? "#FFA500" : "#1A1A1A"}
        lineWidth={isPath ? 5 : isActive ? 4 : 3}
        transparent
        opacity={0.8}
      />
    </group>
  );
}

// Main Graph component
function Graph({ onServiceFound }: { onServiceFound: (service: string) => void }) {
  const { camera, mouse, viewport } = useThree();
  const [searchPath, setSearchPath] = useState<number[]>([]);
  const [highlightedNodes, setHighlightedNodes] = useState<Set<number>>(new Set());
  const [targetNode, setTargetNode] = useState<number | null>(null);
  const [hoveredNode, setHoveredNode] = useState<number | null>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [clickedNodes, setClickedNodes] = useState<Set<number>>(new Set());
  const [clockwiseIndex, setClockwiseIndex] = useState<number>(0);
  const groupRef = useRef<THREE.Group>(null);

  // Generate 2D positions in a circle
  const nodePositions = useMemo(() => {
    const positions: [number, number, number][] = [];
    const radius = 3.5;
    const nodeCount = 10;
    
    for (let i = 0; i < nodeCount; i++) {
      const angle = (i / nodeCount) * Math.PI * 2;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;
      positions.push([x, y, 0.1]); // Nodes slightly above edges
    }
    return positions;
  }, []);

  // Generate edges with more connections but not complete graph
  const edges = useMemo(() => {
    const edgeList: Array<{
      id: string;
      start: [number, number, number];
      end: [number, number, number];
    }> = [];
    
    // Add circular edges (each node connects to its neighbors)
    for (let i = 0; i < nodePositions.length; i++) {
      const nextIndex = (i + 1) % nodePositions.length;
      edgeList.push({
        id: `${i}-${nextIndex}`,
        start: nodePositions[i],
        end: nodePositions[nextIndex]
      });
    }
    
    // Add some additional edges (skip every other node)
    for (let i = 0; i < nodePositions.length; i += 2) {
      const skipIndex = (i + 2) % nodePositions.length;
      if (skipIndex !== i) {
        edgeList.push({
          id: `${i}-${skipIndex}`,
          start: nodePositions[i],
          end: nodePositions[skipIndex]
        });
      }
    }
    
    return edgeList;
  }, [nodePositions]);

  // Handle node click
  const handleNodeClick = useCallback((nodeId: number) => {
    setClickedNodes(prev => {
      const newClicked = new Set(prev);
      if (newClicked.has(nodeId)) {
        newClicked.delete(nodeId);
      } else {
        newClicked.add(nodeId);
      }
      return newClicked;
    });
  }, []);

  // Clockwise color animation
  useEffect(() => {
    const interval = setInterval(() => {
      setClockwiseIndex(prev => (prev + 1) % nodePositions.length);
    }, 800); // Change color every 800ms

    return () => clearInterval(interval);
  }, [nodePositions.length]);

  // Rotation animation that oscillates between 90 degrees
  useFrame((state) => {
    if (groupRef.current) {
      const time = state.clock.getElapsedTime();
      // Oscillate between -90 and +90 degrees (in radians: -π/2 to π/2)
      const rotation = Math.sin(time * 0.5) * Math.PI / 2;
      groupRef.current.rotation.z = rotation;
    }
  });

  // Simulate service search
  const startSearch = useCallback(() => {
    const startNode = Math.floor(Math.random() * nodePositions.length);
    const endNode = Math.floor(Math.random() * nodePositions.length);
    
    if (startNode === endNode) return;
    
    setSearchPath([startNode]);
    setHighlightedNodes(new Set([startNode]));
    setTargetNode(endNode);
    
    // Simulate pathfinding - one node at a time
    let currentNode = startNode;
    const pathInterval = setInterval(() => {
      // Move to next random node
      const nextNode = Math.floor(Math.random() * nodePositions.length);
      if (nextNode !== currentNode) {
        currentNode = nextNode;
        setSearchPath([currentNode]);
        setHighlightedNodes(new Set([currentNode]));
      }
    }, 1000);
    
    // Stop after 5 seconds and fade out
    setTimeout(() => {
      clearInterval(pathInterval);
      setTargetNode(null);
      setHighlightedNodes(new Set());
      setSearchPath([]);
    }, 5000);
  }, [nodePositions.length, onServiceFound]);

  // No mouse tracking

  // No auto-start animation

  return (
    <group ref={groupRef}>
      {/* Render edges */}
      {edges.map((edge, index) => {
        const edgeStart = parseInt(edge.id.split('-')[0]);
        const edgeEnd = parseInt(edge.id.split('-')[1]);
        
        const isPath = searchPath.length > 1 && 
          searchPath.some((nodeId, i) => {
            if (i < searchPath.length - 1) {
              const nextNode = searchPath[i + 1];
              return (nodeId === edgeStart && nextNode === edgeEnd) ||
                     (nodeId === edgeEnd && nextNode === edgeStart);
            }
            return false;
          });
        
        const isActive = highlightedNodes.has(edgeStart) || highlightedNodes.has(edgeEnd);
        
        return (
          <Edge
            key={edge.id}
            start={edge.start}
            end={edge.end}
            isActive={isActive}
            isPath={isPath}
          />
        );
      })}
      
          {/* Render nodes */}
          {nodePositions.map((position, index) => (
            <Node
              key={index}
              position={position}
              id={index}
              isHighlighted={index === clockwiseIndex}
              isTarget={false}
              isClicked={clickedNodes.has(index)}
              onHover={() => setHoveredNode(index)}
              onLeave={() => setHoveredNode(null)}
              onClick={() => handleNodeClick(index)}
            />
          ))}
    </group>
  );
}

// Main Graph3D component
export default function Graph3D({ onServiceFound }: { onServiceFound: (service: string) => void }) {
  return (
    <div className="w-full h-full">
      <Canvas
        camera={{ position: [0, 0, 12], fov: 60 }}
        style={{ background: 'transparent' }}
      >
        <OrbitControls
          enableZoom={true}
          enablePan={false}
          enableRotate={false}
          minDistance={6}
          maxDistance={20}
          autoRotate={false}
        />
        <Graph onServiceFound={onServiceFound} />
      </Canvas>
    </div>
  );
}