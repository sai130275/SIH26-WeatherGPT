import { useState } from 'react';
import { Icon } from '@/components/Icon';
import { mapLayers, timelineLabels, timelineNodes } from '@/data/mockData';

export function MapPage() {
  const [activeLayer, setActiveLayer] = useState('radar');
  const [isPlaying, setIsPlaying] = useState(false);
  const [timelineValue, setTimelineValue] = useState(0);

  const togglePlay = () => {
    if (!isPlaying) {
      setIsPlaying(true);
      const interval = setInterval(() => {
        setTimelineValue((prev) => {
          const next = (prev + 1) % 6;
          if (next === 0) {
            clearInterval(interval);
            setIsPlaying(false);
          }
          return next;
        });
      }, 1500);
    } else {
      setIsPlaying(false);
    }
  };

  return (
    <div className="flex flex-col w-full pb-10">
      {/* Top Search & Controls Bar */}
      <div className="flex items-center gap-space-sm mb-space-md mt-space-sm">
        <div className="flex-grow flex items-center bg-surface-container-high rounded-xl px-space-md py-space-sm gap-space-sm shadow-sm">
          <Icon name="search" size={20} className="text-outline" />
          <input
            className="bg-transparent text-on-surface placeholder:text-outline w-full outline-none text-body-md"
            placeholder="Search region, city, or coordinates..."
            type="text"
            defaultValue="Warangal, Telangana"
          />
          <button className="text-secondary">
            <Icon name="mic" size={18} />
          </button>
        </div>
        <button
          className="w-12 h-12 bg-surface-container-high hover:bg-surface-container-highest text-secondary rounded-xl flex items-center justify-center shadow-sm shrink-0 transition-all active:scale-95"
          title="Center on GPS"
        >
          <Icon name="my_location" size={22} />
        </button>
      </div>

      {/* Layer Selector Pill Bar */}
      <div className="overflow-x-auto no-scrollbar -mx-gutter px-gutter mb-space-md">
        <div className="flex gap-space-xs pb-space-xs shrink-0 w-max">
          {mapLayers.map((layer) => (
            <button
              key={layer.id}
              onClick={() => setActiveLayer(layer.id)}
              className={`flex items-center gap-space-xs px-space-md py-space-sm rounded-full text-label-md transition-all ${
                activeLayer === layer.id
                  ? 'bg-secondary text-on-secondary font-semibold shadow-sm'
                  : 'bg-surface-container-high hover:bg-surface-container-highest text-on-surface-variant'
              }`}
            >
              <Icon name={layer.icon} size={16} filled={activeLayer === layer.id} />
              {layer.label}
            </button>
          ))}
        </div>
      </div>

      {/* Interactive GIS Map Canvas */}
      <div className="relative w-full h-[380px] rounded-xl overflow-hidden bg-surface-container-lowest shadow-lg mb-space-md flex flex-col justify-between p-space-md">
        {/* Map Background */}
        <div
          className="absolute inset-0 bg-cover bg-center opacity-80 mix-blend-luminosity"
          style={{
            backgroundImage:
              "url('https://lh3.googleusercontent.com/aida-public/AB6AXuBHlQYZroRlGr4iFUE6aX7Qp81YXPeBL3lK5LvYSWFc1b-NACMxhNtRJz8CHg4HH0MK1oVKMN_lIL2HPIzzkfREsdf74yXONfGBX_KQib_zR8anRK87zIzqtRO6GApExyNTEtGnOmw8qBXAXNUfdqhNCyWuqbNuxJ-W8xFTGJ3eO8CQ6W0iURaK8y8JuaJGKiJbSXFacsse_IY3Sq2N4SkNQooP4Q9aCCqaZw0o5FUuKBtrlm24xII')",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-tr from-surface-container-lowest/80 via-transparent to-surface-container/60 pointer-events-none" />
        <div className="absolute top-1/4 left-1/3 w-40 h-40 rounded-full bg-secondary-container/20 blur-xl animate-pulse" />
        <div className="absolute top-1/3 left-1/2 w-32 h-32 rounded-full bg-tertiary/30 blur-2xl" />

        {/* Top Map Tools */}
        <div className="relative z-10 flex justify-between items-start">
          <div className="flex flex-col gap-space-xs">
            <span className="bg-surface/90 backdrop-blur-md px-space-sm py-1 rounded-lg text-label-sm font-mono-data text-secondary w-max flex items-center gap-space-xs shadow-sm">
              <span className="w-2 h-2 rounded-full bg-secondary animate-ping" />
              LIVE RADAR • 17:42 IST
            </span>
          </div>
          <div className="flex flex-col gap-space-xs">
            <button className="w-10 h-10 bg-surface/90 hover:bg-surface backdrop-blur-md text-on-surface rounded-xl flex items-center justify-center shadow-sm">
              <Icon name="layers" size={20} />
            </button>
            <button className="w-10 h-10 bg-surface/90 hover:bg-surface backdrop-blur-md text-on-surface rounded-xl flex items-center justify-center shadow-sm">
              <Icon name="zoom_in" size={20} />
            </button>
            <button className="w-10 h-10 bg-surface/90 hover:bg-surface backdrop-blur-md text-on-surface rounded-xl flex items-center justify-center shadow-sm">
              <Icon name="zoom_out" size={20} />
            </button>
          </div>
        </div>

        {/* Active Warning Overlay Card */}
        <div className="relative z-10 bg-error-container/90 backdrop-blur-md p-space-md rounded-xl text-on-error-container shadow-xl animate-bounce-subtle">
          <div className="flex items-start justify-between gap-space-sm mb-space-xs">
            <div className="flex items-center gap-space-sm">
              <div className="w-8 h-8 rounded-lg bg-error flex items-center justify-center text-on-error shrink-0">
                <Icon name="crisis_alert" size={20} filled />
              </div>
              <div>
                <h4 className="text-headline-sm leading-tight font-semibold">Severe Thunderstorm Warning</h4>
                <span className="text-label-sm opacity-90">Warangal Urban & Rural Districts</span>
              </div>
            </div>
            <span className="text-label-sm bg-error px-space-xs py-0.5 rounded text-on-error font-bold uppercase">
              Active
            </span>
          </div>
          <p className="text-body-sm opacity-95 mb-space-sm">
            Severe convective activity detected. Expect wind gusts up to 45 km/h, intense downpours, and localized lightning strikes over the next 90 minutes.
          </p>
          <div className="flex items-center justify-between pt-2 border-t border-error/30 text-label-md">
            <span className="font-mono-data">Valid until 19:15 IST</span>
            <button className="underline font-semibold flex items-center gap-1 hover:opacity-80">
              <span>Evacuation corridors</span>
              <Icon name="arrow_forward" size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Map Legend Card */}
      <div className="bg-surface-container-low rounded-xl p-space-md mb-space-md shadow-sm">
        <div className="flex items-center justify-between mb-space-sm">
          <span className="text-label-md font-semibold uppercase tracking-wider text-on-surface-variant">
            Map Legend & Gradients
          </span>
          <span className="text-label-sm text-secondary font-mono-data">Standard Scale</span>
        </div>
        <div className="grid grid-cols-2 gap-space-md">
          <div>
            <span className="text-label-sm block mb-1 text-on-surface-variant">Rainfall Intensity (mm/h)</span>
            <div className="h-3 w-full rounded-full bg-gradient-to-r from-secondary-fixed-dim via-secondary-container to-error mb-1" />
            <div className="flex justify-between text-label-sm text-outline font-mono-data">
              <span>0.1 mm</span>
              <span>15 mm</span>
              <span>50+ mm</span>
            </div>
          </div>
          <div>
            <span className="text-label-sm block mb-1 text-on-surface-variant">Wind Speed (km/h)</span>
            <div className="h-3 w-full rounded-full bg-gradient-to-r from-surface-variant via-secondary-fixed to-tertiary mb-1" />
            <div className="flex justify-between text-label-sm text-outline font-mono-data">
              <span>10</span>
              <span>30</span>
              <span>60+</span>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline Slider & Playback Controls */}
      <div className="bg-surface-container rounded-xl p-space-md shadow-lg">
        <div className="flex items-center justify-between mb-space-sm">
          <div className="flex items-center gap-space-sm">
            <button
              onClick={togglePlay}
              className={`w-10 h-10 rounded-full flex items-center justify-center shadow-md hover:scale-105 transition-transform active:scale-95 ${
                isPlaying ? 'bg-tertiary text-on-tertiary' : 'bg-secondary text-on-secondary'
              }`}
            >
              <Icon name={isPlaying ? 'pause' : 'play_arrow'} size={20} filled />
            </button>
            <div>
              <span className="text-label-md font-semibold text-on-surface block">Forecast Playback</span>
              <span className="text-label-sm text-secondary font-mono-data">
                {timelineLabels[timelineValue]}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-space-xs">
            <button className="px-space-sm py-1 bg-surface-container-high rounded text-label-sm font-mono-data text-on-surface-variant hover:text-on-surface">
              1x
            </button>
            <button className="px-space-sm py-1 bg-surface-container-high rounded text-label-sm font-mono-data text-on-surface-variant hover:text-on-surface">
              Loop
            </button>
          </div>
        </div>
        <div className="space-y-space-xs mt-space-sm">
          <input
            type="range"
            min={0}
            max={5}
            step={1}
            value={timelineValue}
            onChange={(e) => setTimelineValue(Number(e.target.value))}
            className="w-full accent-secondary cursor-pointer h-2 bg-surface-container-highest rounded-lg appearance-none"
          />
          <div className="flex justify-between text-label-sm text-outline font-mono-data px-1">
            {timelineNodes.map((node, i) => (
              <button
                key={i}
                onClick={() => setTimelineValue(i)}
                className={`cursor-pointer ${
                  timelineValue === i ? 'text-secondary font-bold' : ''
                }`}
              >
                {node}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
