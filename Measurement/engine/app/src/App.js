import React, { Suspense, useRef, useState } from 'react';
import { Canvas, useLoader, useThree, useFrame } from '@react-three/fiber';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
 function Model({ url, color, onClick }) {
  const obj = useLoader(OBJLoader, url);
  const mesh = useRef();
  const [hovered, setHovered] = useState(false);
   obj.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.material.color.set(color);
    }
  });
   useFrame(() => (mesh.current.rotation.y += 0.01)); // Rotate the model
   return (
    <mesh
      ref={mesh}
      onClick={onClick}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      <primitive object={obj} />
      {hovered && (
        <meshLambertMaterial attach="material" color={0xffffff} transparent opacity={0.3} />
      )}
    </mesh>
  );
}
 function Controls() {
  const { camera, gl: { domElement } } = useThree();
  return <OrbitControls camera={camera} domElement={domElement} />;
}
 function Scene() {
  const [color, setColor] = useState(0xe0ac69);
   const handleClick = () => {
    setColor(Math.random() * 0xffffff);
  };
   return (
    <Canvas style={{ background: 'linear-gradient(to bottom, #1e5799, #2989d8, #207cca, #7db9e8)' }}>
      <ambientLight />
      <pointLight position={[10, 10, 10]} /> {/* Add a point light */}
      <Suspense fallback={null}>
        <Model url="/test1.obj" color={color} onClick={handleClick} />
      </Suspense>
      <Controls />
    </Canvas>
  );
}
 function App() {
  return (
    <div style={{ height: '100vh', width: '100vw' }}>
      <Scene />
    </div>
  );
}
 export default App;