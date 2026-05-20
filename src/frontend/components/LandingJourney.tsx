"use client";

import React, { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { Brain, Activity } from "lucide-react";

// Three-stop scroll narrative that lives above the live Mission
// Control surface. The background is a CSS gradient track rather than
// a video file so the page stays brand owned, offline safe, and fast
// on first paint. Drop in /landing-loop.mp4 under public/ and swap
// the BackgroundCanvas if you want a real video later.

function BackgroundCanvas({ progress }: { progress: ReturnType<typeof useScroll>["scrollYProgress"] }) {
  // Drift the radial gradient across the viewport so the canvas feels
  // alive without a video file.
  const x = useTransform(progress, [0, 1], ["20%", "80%"]);
  const y = useTransform(progress, [0, 1], ["30%", "70%"]);
  const hue1 = useTransform(progress, [0, 0.5, 1], ["#ff1801", "#ff4a1a", "#00f0ff"]);
  const hue2 = useTransform(progress, [0, 0.5, 1], ["#0a0a0a", "#13161c", "#050505"]);
  return (
    <motion.div
      className="absolute inset-0"
      style={{
        background: useTransform(
          [x, y, hue1, hue2],
          ([xv, yv, h1, h2]) => `radial-gradient(circle at ${xv} ${yv}, ${h1}33 0%, ${h2} 60%)`,
        ),
      }}
    />
  );
}

export function LandingJourney() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  const text1Opacity = useTransform(scrollYProgress, [0, 0.15, 0.25, 0.35], [1, 1, 0, 0]);
  const text1Y = useTransform(scrollYProgress, [0, 0.25], [0, -50]);

  const text2Opacity = useTransform(scrollYProgress, [0.3, 0.4, 0.55, 0.65], [0, 1, 1, 0]);
  const text2Y = useTransform(scrollYProgress, [0.3, 0.4], [50, 0]);

  const text3Opacity = useTransform(scrollYProgress, [0.6, 0.7, 0.9, 1], [0, 1, 1, 0]);
  const text3Y = useTransform(scrollYProgress, [0.6, 0.7], [50, 0]);

  return (
    <div ref={containerRef} className="relative w-full h-[400vh]">
      <div className="fixed top-0 left-0 w-full h-screen overflow-hidden bg-[#0a0a0a] z-0 pointer-events-none">
        <BackgroundCanvas progress={scrollYProgress} />
        <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-black/20 to-black/80" />
      </div>

      <div className="absolute top-0 left-0 w-full h-full pointer-events-none z-10">
        {/* Scene 1: NeuroPit identity */}
        <div className="absolute top-0 w-full h-screen flex flex-col items-center justify-center">
          <motion.div style={{ opacity: text1Opacity, y: text1Y }} className="text-center px-4">
            <div className="flex items-center justify-center gap-4 mb-6">
              <Brain className="text-apex-red w-12 h-12 md:w-16 md:h-16 apex-glow-red rounded-full" />
              <Activity className="text-apex-red w-12 h-12 md:w-16 md:h-16 apex-glow-red rounded-full" />
            </div>
            <h1 className="text-5xl md:text-8xl font-black tracking-[0.2em] uppercase text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-500 mb-6 font-display">
              NeuroPit
            </h1>
            <p className="text-xs md:text-sm font-sans text-gray-400 tracking-[0.4em] uppercase">
              Cognitive Twin Operating System &middot; IBM AI Builders Challenge 2026
            </p>
          </motion.div>
        </div>

        {/* Scene 2: thesis */}
        <div className="absolute top-[100vh] w-full h-screen flex flex-col items-center justify-center">
          <motion.div
            style={{ opacity: text2Opacity, y: text2Y }}
            className="text-center px-4 max-w-4xl mx-auto"
          >
            <h2 className="text-3xl md:text-5xl font-display font-bold tracking-[0.1em] uppercase text-white mb-6 leading-tight">
              Telemetry is infrastructure.
              <br />
              <span className="text-apex-red drop-shadow-[0_0_8px_rgba(255,24,1,0.6)]">
                Cognition is the product.
              </span>
            </h2>
            <p className="text-sm md:text-xl font-sans text-gray-400 tracking-[0.2em] uppercase leading-relaxed">
              We don&apos;t optimise the car. We infer the driver&apos;s nervous system in real time.
            </p>
          </motion.div>
        </div>

        {/* Scene 3: trust */}
        <div className="absolute top-[200vh] w-full h-screen flex flex-col items-center justify-center">
          <motion.div
            style={{ opacity: text3Opacity, y: text3Y }}
            className="text-center px-4 max-w-4xl mx-auto"
          >
            <h2 className="text-3xl md:text-5xl font-display font-bold tracking-[0.1em] uppercase text-white mb-6">
              A defensible audit trail.
            </h2>
            <p className="text-sm md:text-xl font-sans text-gray-400 tracking-[0.2em] uppercase leading-relaxed">
              Grounded in IBM Granite explainable reasoning. Built for the pit wall.
            </p>
          </motion.div>
        </div>

        {/* Scene 4: scroll-to-mission-control nudge */}
        <div className="absolute top-[300vh] w-full h-screen flex flex-col items-center justify-center">
          <motion.div
            style={{ opacity: text3Opacity }}
            className="text-center px-4 max-w-4xl mx-auto"
          >
            <p className="text-xs md:text-sm font-sans text-gray-500 tracking-[0.4em] uppercase mb-4">
              Live Mission Control below
            </p>
            <div className="w-[1px] h-16 mx-auto bg-gradient-to-b from-apex-cyan to-transparent" />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
