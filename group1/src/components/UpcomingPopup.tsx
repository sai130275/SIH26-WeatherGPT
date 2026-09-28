import { useState, useRef, useEffect, ReactNode } from 'react';
import { Icon } from './Icon';

interface UpcomingPopupProps {
  children: ReactNode;
  featureName: string;
  className?: string;
}

export function UpcomingPopup({ children, featureName, className = '' }: UpcomingPopupProps) {
  const [isOpen, setIsOpen] = useState(false);
  const triggerRef = useRef<HTMLDivElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ top: 0, left: 0, opacity: 0 });

  const calculatePosition = () => {
    if (!triggerRef.current || !popupRef.current) return;
    const triggerRect = triggerRef.current.getBoundingClientRect();
    const popupRect = popupRef.current.getBoundingClientRect();

    const margin = 12;
    const offset = 8;
    
    // Default down-right
    let top = triggerRect.bottom + offset;
    let left = triggerRect.right + offset;

    // Viewport bounds
    const vh = window.innerHeight;
    const vw = window.innerWidth;

    let overflowsRight = (left + popupRect.width + margin) > vw;
    let overflowsBottom = (top + popupRect.height + margin) > vh;

    if (overflowsRight && overflowsBottom) {
      // up-left
      top = triggerRect.top - offset - popupRect.height;
      left = triggerRect.left - offset - popupRect.width;
    } else if (overflowsRight) {
      // down-left
      top = triggerRect.bottom + offset;
      left = triggerRect.left - offset - popupRect.width;
    } else if (overflowsBottom) {
      // up-right
      top = triggerRect.top - offset - popupRect.height;
      left = triggerRect.right + offset;
    }

    // clamping
    if (left < margin) left = margin;
    if (top < margin) top = margin;
    if (left + popupRect.width + margin > vw) left = vw - popupRect.width - margin;
    if (top + popupRect.height + margin > vh) top = vh - popupRect.height - margin;

    setPos({ top, left, opacity: 1 });
  };

  useEffect(() => {
    if (!isOpen) {
      setPos(p => ({ ...p, opacity: 0 }));
      return;
    }
    
    // initial pos
    calculatePosition();
    
    // scroll / resize listeners
    const handleScroll = () => {
      calculatePosition();
    };
    
    window.addEventListener('scroll', handleScroll, true); // true for capturing scroll in any container
    window.addEventListener('resize', handleScroll);
    
    return () => {
      window.removeEventListener('scroll', handleScroll, true);
      window.removeEventListener('resize', handleScroll);
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (
        triggerRef.current && !triggerRef.current.contains(e.target as Node) &&
        popupRef.current && !popupRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  return (
    <>
      <div 
        ref={triggerRef} 
        onClick={(e) => {
           e.preventDefault();
           e.stopPropagation();
           setIsOpen(!isOpen);
        }}
        className={`inline-block cursor-pointer relative ${className}`}
      >
        <div className="pointer-events-none w-full h-full">
          {children}
        </div>
      </div>
      {isOpen && (
        <div
          ref={popupRef}
          style={{
            position: 'fixed',
            top: pos.top,
            left: pos.left,
            opacity: pos.opacity,
            zIndex: 9999,
            maxWidth: 'calc(100vw - 24px)',
            pointerEvents: pos.opacity === 0 ? 'none' : 'auto'
          }}
          className="bg-surface-container-high rounded-xl p-space-md shadow-xl border border-outline-variant/50 flex flex-col gap-space-xs transition-opacity duration-150 ease-out min-w-[240px] max-w-[300px]"
        >
          <div className="flex items-center justify-between gap-space-sm mb-1">
            <h4 className="font-headline-sm text-on-surface">Coming Soon</h4>
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <Icon name="construction" size={18} />
            </div>
          </div>
          <p className="text-body-md text-on-surface-variant leading-relaxed">
            <strong className="text-on-surface font-medium block mb-1">{featureName}</strong>
            This feature is planned for an upcoming release.
          </p>
        </div>
      )}
    </>
  );
}
