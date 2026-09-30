import { useState, useRef, useEffect } from 'react';
import { Icon } from '@/components/Icon';
import { UpcomingPopup } from '@/components/UpcomingPopup';
import { supabase } from '@/lib/supabase';
import { usePreferences } from '@/context/PreferencesContext';
import { formatWind, formatPrecip } from '@/utils/units';

interface RichAIData {
  confidence: string;
  timestamp: string;
  alertTitle: string;
  summary: string;
  floodRisk: { level: string; percent: number };
  lightningRisk: { level: string; percent: number };
  hourlyRain: { hour: string; height: string; type: 'low' | 'med' | 'high' }[];
  peak: string;
  recommendedAction: string;
  source: string;
}

interface ChatItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isVoice?: boolean;
  richData?: RichAIData;
  intent?: string;
  sources?: string[];
  isLoading?: boolean;
  isError?: boolean;
}

const getDefaultRichData = (preferences: any): RichAIData => ({
  confidence: '94% Confidence',
  timestamp: 'Warangal • Today, 14:15 IST',
  alertTitle: 'Severe Thunderstorm Alert',
  summary:
    `Yes, heavy thunderstorms expected between 3 PM and 7 PM with 85% probability. Expect wind gusts up to ${formatWind(45, preferences)}.`,
  floodRisk: { level: 'Moderate', percent: 55 },
  lightningRisk: { level: 'High', percent: 85 },
  hourlyRain: [
    { hour: '12h', height: 'h-4', type: 'low' },
    { hour: '13h', height: 'h-6', type: 'low' },
    { hour: '14h', height: 'h-12', type: 'med' },
    { hour: '15h', height: 'h-full', type: 'high' },
    { hour: '16h', height: 'h-[80%]', type: 'high' },
    { hour: '17h', height: 'h-8', type: 'med' },
    { hour: '18h', height: 'h-3', type: 'low' },
  ],
  peak: `${formatPrecip(24, preferences)}/h`,
  recommendedAction:
    'Secure loose outdoor items, delay farm spraying immediately, and avoid open water bodies or tall trees until 18:00 IST.',
  source: 'Open-Meteo Consensus',
});

const initialChat: ChatItem[] = [
  {
    id: 'msg-1',
    role: 'assistant',
    content: 'Hello! I am WeatherGPT Orchestrator. Ask me about weather, travel safety, or crop advisory in Warangal.',
  },
];

import { apiClient } from '@/lib/api';
import type { ApiBaseResponse, ChatRequest, ChatResponse } from '@/types/api';
import { AxiosError } from 'axios';

export function AskAIPage() {
  const { preferences } = usePreferences();
  const [messages, setMessages] = useState<ChatItem[]>(initialChat);
  const [inputVal, setInputVal] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<File | null>(null);
  const [showAttachmentMenu, setShowAttachmentMenu] = useState(false);

  const chatStreamRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const docInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const stopRecognition = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
        recognitionRef.current.abort();
      } catch (e) {}
      
      // Aggressively remove listeners
      recognitionRef.current.onstart = null;
      recognitionRef.current.onresult = null;
      recognitionRef.current.onerror = null;
      recognitionRef.current.onend = null;
      
      recognitionRef.current = null;
    }
    setIsListening(false);
  };

  // Cleanup microphone on unmount
  useEffect(() => {
    return () => {
      stopRecognition();
    };
  }, []);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleToggleListening = () => {
    // If currently listening or a ref exists, stop and destroy it immediately
    if (isListening || recognitionRef.current) {
      stopRecognition();
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      showToast('Voice input is not supported in this browser.');
      return;
    }

    // Always create a fresh instance for a single controlled lifecycle
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      
      if (finalTranscript) {
        setInputVal(prev => (prev ? prev + ' ' + finalTranscript : finalTranscript));
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error', event.error);
      if (event.error === 'not-allowed') {
        showToast('Microphone permission denied.');
      } else if (event.error === 'no-speech') {
        showToast('No speech detected. Try again.');
      }
      stopRecognition();
    };

    recognition.onend = () => {
      stopRecognition();
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch (err) {
      console.error('Failed to start recognition', err);
      stopRecognition();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      showToast('Unsupported file type. Please select PNG, JPG, or WEBP.');
      return;
    }

    setSelectedImage(file);
    setShowAttachmentMenu(false);
    showToast('Image analysis coming soon. Backend does not yet support images.');
  };

  const handleDocChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedDocument(file);
    setShowAttachmentMenu(false);
    showToast('Document analysis coming soon. Backend does not yet support documents.');
  };

  const handleSendMessage = (textToSend?: string, isVoiceInput = false) => {
    // Stop recognition if active before sending
    if (recognitionRef.current || isListening) {
      stopRecognition();
    }

    const text = (textToSend !== undefined ? textToSend : inputVal).trim();
    
    // If no text, and no files, do nothing
    if (!text && !selectedImage && !selectedDocument) return;

    // If only files, show toast and do nothing because backend needs text
    if (!text && (selectedImage || selectedDocument)) {
      showToast('Please add a text query for your attachment.');
      return;
    }

    // Clear files since they aren't fully supported yet
    if (selectedImage) setSelectedImage(null);
    if (selectedDocument) setSelectedDocument(null);

    const userMsgId = `user-${Date.now()}`;
    const newMsg: ChatItem = {
      id: userMsgId,
      role: 'user',
      content: text,
      isVoice: isVoiceInput,
    };

    setMessages((prev) => [...prev, newMsg]);
    if (textToSend === undefined) {
      setInputVal('');
    }

    // Save to Supabase with try-catch
    (async () => {
      try {
        await supabase.from('chat_messages').insert({ role: 'user', content: text, language: 'en' });
      } catch (err) {
        console.warn('Chat message storage offline or skipped:', err);
      }
    })();

    // Real API Call
    (async () => {
      setIsTyping(true);
      const loadingId = `loading-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        { id: loadingId, role: 'assistant', content: '...', isLoading: true },
      ]);

      try {
        const payload: ChatRequest = {
          message: text,
          latitude: 17.9689,
          longitude: 79.5941,
          language: 'en',
        };

        const response = await apiClient.post<ApiBaseResponse<ChatResponse>>('/chat', payload);
        const data = response.data.data;

        const aiResponse: ChatItem = {
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: data.answer,
          intent: data.intent,
          sources: data.sources,
        };

        setMessages((prev) => prev.map((msg) => (msg.id === loadingId ? aiResponse : msg)));

        try {
          await supabase.from('chat_messages').insert({
            role: 'assistant',
            content: data.answer,
            language: 'en',
          });
        } catch (err) {
          console.warn('AI response storage skipped:', err);
        }
      } catch (err: unknown) {
        const axiosErr = err as AxiosError<ApiBaseResponse<null>>;
        // Unmask structured gateway error message if present (e.g. rate limits or upstream timeouts)
        // instead of defaulting immediately to a generic network error.
        const errorResponse: ChatItem = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content:
            axiosErr.response?.data?.error?.message ||
            axiosErr.response?.data?.message ||
            'Network error: Failed to connect to the intelligence gateway.',
          isError: true,
        };
        setMessages((prev) => prev.map((msg) => (msg.id === loadingId ? errorResponse : msg)));
      } finally {
        setIsTyping(false);
      }
    })();
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: 'WeatherGPT Advisory',
        text: 'Severe Thunderstorm Alert for Warangal: Heavy thunder expected 3 PM - 7 PM. Stay safe!',
      }).catch(() => {});
    } else {
      navigator.clipboard?.writeText(
        'WeatherGPT Advisory: Heavy thunderstorms expected in Warangal between 3 PM and 7 PM with 85% probability.'
      );
      showToast('Advisory copied to clipboard!');
    }
  };

  return (
    <div className="flex flex-col w-full pb-24">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 bg-on-surface text-surface px-space-md py-2 rounded-xl text-body-sm shadow-xl animate-fade-in">
          {toastMessage}
        </div>
      )}

      {/* Model Indicator Header */}
      <div className="flex items-center justify-between mb-space-md px-space-xs py-2 bg-surface-container rounded-xl shadow-sm">
        <div className="flex items-center gap-space-sm">
          <span className="w-2.5 h-2.5 rounded-full bg-secondary animate-pulse" />
          <span className="text-label-sm font-mono-data text-secondary">WeatherGPT-Orchestrator v4.2</span>
        </div>
        <span className="text-label-sm text-on-surface-variant bg-surface-container-highest px-space-sm py-0.5 rounded-lg">
          IMD + ECMWF RAG
        </span>
      </div>

      {/* Voice-First Hero / Mic Button for Speech Input */}
      <div className="relative overflow-hidden bg-gradient-to-br from-surface-container via-surface-container-high to-surface-container-low rounded-2xl p-space-lg mb-space-lg shadow-xl text-center">
        <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-secondary/10 rounded-full blur-2xl pointer-events-none" />
        <div className="absolute -left-10 -top-10 w-40 h-40 bg-tertiary/10 rounded-full blur-2xl pointer-events-none" />
        <span className="text-label-md text-on-surface-variant uppercase tracking-wider block mb-space-xs">
          Voice Assistant Ready
        </span>
        <h2 className="text-headline-md text-on-surface mb-space-md">Ask in English</h2>
        <div className="flex justify-center items-center my-space-md">
          <button
            onClick={handleToggleListening}
            className={`relative group w-20 h-20 rounded-full flex items-center justify-center shadow-lg transition-all duration-300 transform active:scale-95 cursor-pointer ${
              isListening ? 'bg-error text-on-error animate-pulse' : 'bg-secondary-container hover:bg-secondary text-on-secondary-container'
            }`}
          >
            <span className="absolute inset-0 rounded-full bg-secondary/30 animate-ping opacity-75" />
            <Icon name="mic" size={36} />
          </button>
        </div>
        <p className="text-body-sm text-on-surface-variant">
          {isListening ? (
            <span className="text-error font-medium animate-pulse">Listening... (English)</span>
          ) : (
            <>
              Tap to speak (e.g., <span className="text-secondary italic">"Will it rain tomorrow?"</span>)
            </>
          )}
        </p>
      </div>

      {/* Quick Prompt Pills */}
      <div className="mb-space-lg">
        <span className="text-label-md text-on-surface-variant block mb-space-sm">Suggested Queries</span>
        <div className="flex gap-space-sm overflow-x-auto pb-space-xs no-scrollbar">
          {[
            'Will it rain tomorrow?',
            'Is it safe to travel?',
            'When to irrigate crop?',
            'Explain weather in Telugu',
          ].map((prompt) => (
            <button
              key={prompt}
              onClick={() => handleSendMessage(prompt)}
              className="whitespace-nowrap bg-surface-container-high hover:bg-surface-variant text-on-surface text-body-sm px-space-md py-space-sm rounded-xl transition-all"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Conversation Stream */}
      <div ref={chatStreamRef} className="flex flex-col gap-space-lg mb-20" id="chat-stream">
        {messages.map((msg) => {
          if (msg.role === 'user') {
            return (
              <div key={msg.id} className="flex justify-end">
                <div className="bg-secondary text-on-secondary max-w-[85%] rounded-2xl rounded-tr-none p-space-md shadow-md">
                  <div className="flex items-center gap-space-xs mb-1 justify-end text-on-secondary/80 text-label-sm">
                    <span>You</span>
                    <Icon name={msg.isVoice ? 'mic' : 'chat'} size={14} />
                  </div>
                  <p className="text-body-md font-medium">{msg.content}</p>
                </div>
              </div>
            );
          }

          // Assistant Message
          if (msg.richData) {
            const data = msg.richData;
            return (
              <div key={msg.id} className="flex justify-start">
                <div className="bg-surface-container rounded-2xl rounded-tl-none max-w-[95%] w-full p-space-md shadow-xl flex flex-col gap-space-md">
                  {/* Header / Metadata */}
                  <div className="flex items-center justify-between border-b border-surface-variant/40 pb-space-sm">
                    <div className="flex items-center gap-space-xs">
                      <div className="w-7 h-7 rounded-lg bg-secondary-container flex items-center justify-center text-on-secondary-container">
                        <Icon name="smart_toy" size={16} />
                      </div>
                      <div>
                        <span className="text-label-md text-on-surface font-semibold block">
                          WeatherGPT Orchestrator
                        </span>
                        <span className="text-label-sm text-on-surface-variant font-mono-data">
                          {data.timestamp}
                        </span>
                      </div>
                    </div>
                    <span className="bg-emerald-500/20 text-emerald-400 text-label-sm px-2 py-0.5 rounded font-mono-data">
                      {data.confidence}
                    </span>
                  </div>

                  {/* Direct Answer */}
                  <div>
                    <h3 className="text-headline-sm text-on-surface mb-space-xs">{data.alertTitle}</h3>
                    <p className="text-body-md text-on-surface-variant leading-relaxed">
                      {data.summary}
                    </p>
                  </div>

                  {/* Risk Meters & Mini Chart Grid */}
                  <div className="grid grid-cols-2 gap-space-md bg-surface-container-low p-space-md rounded-xl">
                    {/* Flood Risk */}
                    <div className="flex flex-col gap-1">
                      <div className="flex justify-between items-center text-label-sm">
                        <span className="text-on-surface-variant">Flood Risk</span>
                        <span className="text-amber-400 font-mono-data font-semibold">
                          {data.floodRisk.level}
                        </span>
                      </div>
                      <div className="w-full bg-surface-variant h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-amber-400 h-full rounded-full transition-all duration-500"
                          style={{ width: `${data.floodRisk.percent}%` }}
                        />
                      </div>
                    </div>

                    {/* Lightning Risk */}
                    <div className="flex flex-col gap-1">
                      <div className="flex justify-between items-center text-label-sm">
                        <span className="text-on-surface-variant">Lightning Risk</span>
                        <span className="text-error font-mono-data font-semibold">
                          {data.lightningRisk.level}
                        </span>
                      </div>
                      <div className="w-full bg-surface-variant h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-error h-full rounded-full transition-all duration-500"
                          style={{ width: `${data.lightningRisk.percent}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Mini Rain Accumulation Sparkline / Bar Chart */}
                  <div className="bg-surface-container-low p-space-md rounded-xl">
                    <div className="flex justify-between items-center mb-space-sm">
                      <span className="text-label-md text-on-surface-variant">Hourly Rain Accumulation ({preferences?.precip_unit || 'mm'})</span>
                      <span className="text-label-sm font-mono-data text-secondary">Peak: {data.peak}</span>
                    </div>
                    <div className="flex items-end justify-between h-16 pt-2 gap-2">
                      {data.hourlyRain.map((bar, idx) => {
                        const isSevere = bar.type === 'high';
                        const isMed = bar.type === 'med';
                        const barColor = isSevere
                          ? 'bg-error-container hover:bg-error'
                          : isMed
                          ? 'bg-secondary-container hover:bg-secondary'
                          : 'bg-surface-variant hover:bg-secondary/40';

                        const textColor = isSevere
                          ? 'text-on-error-container font-bold'
                          : isMed
                          ? 'text-on-secondary-container font-bold'
                          : 'text-on-surface-variant';

                        return (
                          <div
                            key={idx}
                            className={`flex-1 ${barColor} rounded-t ${bar.height} flex flex-col justify-end items-center transition-all`}
                          >
                            <span className={`text-[9px] font-mono-data ${textColor} mb-1`}>{bar.hour}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Recommended Action Box */}
                  <div className="bg-surface-container-highest/80 border-l-4 border-secondary p-space-md rounded-r-xl">
                    <div className="flex items-center gap-space-xs text-secondary mb-1">
                      <Icon name="verified_user" size={18} />
                      <span className="text-label-md font-semibold uppercase tracking-wider">
                        Recommended Action
                      </span>
                    </div>
                    <p className="text-body-sm text-on-surface">{data.recommendedAction}</p>
                  </div>

                  {/* Source Footer */}
                  <div className="flex items-center justify-between pt-2 border-t border-surface-variant/30 text-label-sm text-on-surface-variant">
                    <span>Source: {data.source}</span>
                    <button
                      onClick={handleShare}
                      className="flex items-center gap-1 text-secondary hover:underline cursor-pointer"
                    >
                      <Icon name="share" size={14} />
                      <span>Share</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          }

          // Standard Assistant Bubble
          return (
            <div key={msg.id} className="flex justify-start">
              <div className={`rounded-2xl rounded-tl-none max-w-[95%] w-full p-space-md shadow-xl flex flex-col gap-space-md ${msg.isError ? 'bg-error-container text-on-error-container' : 'bg-surface-container'}`}>
                <div className="flex items-center justify-between border-b border-surface-variant/40 pb-space-sm">
                  <div className="flex items-center gap-space-xs">
                    <div className="w-7 h-7 rounded-lg bg-secondary-container flex items-center justify-center text-on-secondary-container">
                      <Icon name={msg.isError ? 'error' : 'smart_toy'} size={16} />
                    </div>
                    <div>
                      <span className="text-label-md text-on-surface font-semibold block">
                        WeatherGPT Orchestrator
                      </span>
                      <span className="text-label-sm text-on-surface-variant font-mono-data">
                        Live RAG Query • Just now
                      </span>
                    </div>
                  </div>
                  {msg.intent && (
                    <span className="bg-secondary/20 text-secondary text-label-sm px-2 py-0.5 rounded font-mono-data uppercase">
                      {msg.intent}
                    </span>
                  )}
                </div>
                <div>
                  <p className={`text-body-md leading-relaxed ${msg.isError ? 'text-error' : 'text-on-surface'}`}>
                    {msg.isLoading ? (
                      <span className="animate-pulse">Thinking...</span>
                    ) : (
                      msg.content
                    )}
                  </p>
                </div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="bg-surface-container-high/60 p-space-sm rounded-xl text-label-sm text-on-surface-variant">
                    <span>Sources: {msg.sources.join(', ')}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom Input Bar (Fixed just above bottom navigation) */}
      <div className="fixed bottom-20 inset-x-0 z-40 px-gutter bg-surface/95 backdrop-blur-lg py-3">
        <div className="max-w-4xl mx-auto flex items-center gap-space-sm bg-surface-container-high p-1.5 rounded-2xl shadow-2xl border border-surface-variant/40 relative">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/png, image/jpeg, image/jpg, image/webp"
            className="hidden"
          />
          <input
            type="file"
            ref={docInputRef}
            onChange={handleDocChange}
            accept=".pdf,.doc,.docx,.txt"
            className="hidden"
          />
          
          <button
            onClick={() => setShowAttachmentMenu(true)}
            className="w-11 h-11 flex items-center justify-center text-on-surface-variant hover:text-on-surface rounded-xl hover:bg-surface-variant/50 transition-all cursor-pointer shrink-0"
            title="Attach file"
          >
            <Icon name="attach_file" size={20} />
          </button>

          {/* Attachment Menu */}
          {showAttachmentMenu && (
            <>
              <div className="fixed inset-0 z-40 cursor-default" onClick={() => setShowAttachmentMenu(false)} />
              <div className="absolute bottom-[calc(100%+0.5rem)] left-0 w-56 bg-surface rounded-xl p-2 shadow-xl border border-outline-variant/30 z-50 flex flex-col gap-1 origin-bottom-left animate-in fade-in zoom-in-95 duration-200">
                <UpcomingPopup featureName="Image Upload">
                  <button
                    className="w-full px-3 py-2 rounded-lg text-left text-body-md hover:bg-surface-variant text-on-surface flex items-center gap-2"
                  >
                    <Icon name="image" size={18} />
                    Upload Image
                  </button>
                </UpcomingPopup>
                <UpcomingPopup featureName="Document Upload">
                  <button
                    className="w-full px-3 py-2 rounded-lg text-left text-body-md hover:bg-surface-variant text-on-surface flex items-center gap-2"
                  >
                    <Icon name="description" size={18} />
                    Upload File
                  </button>
                </UpcomingPopup>
                <UpcomingPopup featureName="Image Analysis">
                  <div
                    className="w-full px-3 py-2 rounded-lg text-left text-body-md hover:bg-surface-variant text-on-surface flex items-center gap-2"
                  >
                    <Icon name="psychology" size={18} />
                    Image Analysis
                  </div>
                </UpcomingPopup>
              </div>
            </>
          )}

          {selectedImage && (
            <div className="relative flex items-center ml-1 shrink-0">
              <div className="w-9 h-9 rounded-lg overflow-hidden border border-surface-variant shadow-sm">
                <img src={URL.createObjectURL(selectedImage)} alt="Preview" className="w-full h-full object-cover" />
              </div>
              <button 
                onClick={() => setSelectedImage(null)}
                className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-error text-on-error flex items-center justify-center cursor-pointer shadow-md z-10 hover:bg-error/90"
              >
                <Icon name="close" size={12} />
              </button>
            </div>
          )}

          {selectedDocument && (
            <div className="relative flex items-center ml-1 shrink-0 bg-surface-variant rounded-lg p-1.5 px-3 border border-surface-variant/50 shadow-sm">
              <Icon name="description" size={16} className="text-primary mr-2" />
              <span className="text-label-sm text-on-surface max-w-[100px] truncate">{selectedDocument.name}</span>
              <button 
                onClick={() => setSelectedDocument(null)}
                className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-error text-on-error flex items-center justify-center cursor-pointer shadow-md z-10 hover:bg-error/90"
              >
                <Icon name="close" size={12} />
              </button>
            </div>
          )}

          <input
            className="flex-1 bg-transparent border-none text-on-surface placeholder:text-on-surface-variant text-body-md focus:outline-none px-space-xs"
            id="chat-input"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSendMessage();
              if (e.key === 'Escape') setShowAttachmentMenu(false);
            }}
            placeholder="Ask about weather, crops, safety..."
            type="text"
          />
          <button
            onClick={handleToggleListening}
            disabled={isTyping}
            className={`w-11 h-11 flex items-center justify-center rounded-xl transition-all ${
              isListening ? 'text-error bg-error/10' : 'text-secondary hover:bg-secondary/10'
            } disabled:opacity-50`}
            title="Voice input"
          >
            <Icon name="mic" size={20} />
          </button>
          <button
            onClick={() => handleSendMessage()}
            disabled={isTyping}
            className="w-11 h-11 bg-secondary text-on-secondary rounded-xl flex items-center justify-center hover:opacity-90 transition-all shadow-md cursor-pointer disabled:opacity-50"
            title="Send query"
          >
            <Icon name="send" size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
