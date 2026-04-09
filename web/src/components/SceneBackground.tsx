import { Canvas, useFrame } from "@react-three/fiber";
import { Grid, PerspectiveCamera, Stars } from "@react-three/drei";
import { useRef } from "react";
import type { Mesh } from "three";

function CyberGrid() {
  return (
    <Grid
      infiniteGrid
      fadeDistance={45}
      fadeStrength={4}
      sectionColor="#00f5ff"
      cellColor="#ff2bd6"
      sectionThickness={1.1}
      cellThickness={0.55}
      position={[0, -2.2, 0]}
      args={[24, 24]}
    />
  );
}

function WireOrb() {
  const ref = useRef<Mesh>(null);
  useFrame((state) => {
    const m = ref.current;
    if (!m) return;
    m.rotation.x = state.clock.elapsedTime * 0.07;
    m.rotation.y = state.clock.elapsedTime * 0.11;
    m.position.y = Math.sin(state.clock.elapsedTime * 0.4) * 0.15;
  });
  return (
    <mesh ref={ref} position={[3.2, 0.6, -7]} scale={2.2}>
      <icosahedronGeometry args={[1, 1]} />
      <meshBasicMaterial
        color="#00f5ff"
        wireframe
        transparent
        opacity={0.12}
      />
    </mesh>
  );
}

export function SceneBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10">
      <Canvas
        gl={{ alpha: true, antialias: true, powerPreference: "high-performance" }}
        dpr={[1, 1.75]}
      >
        <color attach="background" args={["#030508"]} />
        <PerspectiveCamera makeDefault position={[0, 1.8, 11]} fov={52} />
        <ambientLight intensity={0.25} />
        <CyberGrid />
        <Stars
          radius={90}
          depth={42}
          count={5000}
          factor={2.8}
          saturation={0}
          fade
          speed={0.35}
        />
        <WireOrb />
      </Canvas>
    </div>
  );
}
