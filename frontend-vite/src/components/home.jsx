// src/components/ui/Home.jsx
import React from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="min-h-[calc(100vh-64px)] relative overflow-hidden">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-b from-rose-100 via-orange-50 to-amber-100" />
      {/* Soft radial glow */}
      <div className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 h-[40rem] w-[40rem] rounded-full bg-white/40 blur-3xl opacity-50" />

      <section className="relative z-10 mx-auto max-w-4xl px-6 pt-16 pb-10 text-center">
        <p className="text-sm tracking-wide text-gray-700 uppercase animate-fade-in-up" style={{ animationDelay: '100ms' }}>About us</p>
        <h1 className="mt-2 text-4xl md:text-5xl font-extrabold text-gray-900 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
          We’re committed to healthier skin for you
        </h1>
        <p className="mt-4 text-lg md:text-xl text-gray-700 animate-fade-in-up" style={{ animationDelay: '300ms' }}>
          Feel unsure about a skin lesion? Upload a picture now and our model will
          give you guidance on severity and whether to see a dermatologist.
        </p>

        <div className="mt-10 flex justify-center animate-fade-in-up" style={{ animationDelay: '400ms' }}>
          <Link to="/analyze">
            <Button size="lg" className="px-8 py-6 text-lg rounded-2xl shadow-lg">
              Test now for free
            </Button>
          </Link>
        </div>

       <p className="mt-12 text-xs text-gray-600 animate-fade-in-up" style={{ animationDelay: '500ms' }}>
          Demo only — not a medical diagnosis. Always consult a clinician for advice.
        </p>
      </section>
    </div>
  );
}
