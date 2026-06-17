import React, { useState, useRef, useEffect } from 'react';
import { API_BASE } from '@/lib/api';

export default function ChatInterface({ userId }: { userId: string }) {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, session_id: 'session-1', message: input }),
      });

      if (!response.body) throw new Error('No readable stream');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        
        setMessages(prev => {
          const newMessages = [...prev];
          const lastIndex = newMessages.length - 1;
          newMessages[lastIndex] = {
            ...newMessages[lastIndex],
            content: newMessages[lastIndex].content + chunk
          };
          return newMessages;
        });
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error communicating with the server.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 relative z-10 w-full h-full">
      <section className="flex-1 overflow-y-auto px-margin py-xl space-y-xl flex flex-col scroll-smooth">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-on-surface-variant opacity-60">
            <div className="w-16 h-16 border border-outline-variant rounded-xl mb-4 flex items-center justify-center bg-surface-container-low">
              <span className="material-symbols-outlined text-[32px]">terminal</span>
            </div>
            <p className="font-code-md text-code-md">Awaiting protocols...</p>
          </div>
        ) : (
          messages.map((msg, i) => (
            msg.role === 'user' ? (
              <div key={i} className="flex flex-col items-end gap-sm max-w-[85%] ml-auto">
                <div className="bg-primary-container p-md rounded-xl rounded-tr-none text-white shadow-lg">
                  <p className="font-body-md text-body-md">{msg.content}</p>
                </div>
                <span className="font-code-sm text-code-sm text-on-surface-variant opacity-40 px-1">Delivered</span>
              </div>
            ) : (
              <div key={i} className="flex flex-col items-start gap-sm max-w-[85%] animate-fade-in">
                <div className="flex items-center gap-xs mb-1">
                  <span className="font-code-sm text-code-sm text-primary font-bold">HJ_AGENT</span>
                  <span className="font-body-sm text-body-sm text-on-surface-variant opacity-40">System Architect</span>
                </div>
                <div className="bg-surface-container-low border border-outline-variant p-md rounded-xl rounded-tl-none text-on-surface">
                  <p className="font-body-md text-body-md whitespace-pre-wrap font-code-sm leading-relaxed">{msg.content}</p>
                </div>
              </div>
            )
          ))
        )}
        
        {loading && (
          <div className="flex items-center gap-md py-md">
            <div className="flex gap-1">
              <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
              <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{animationDelay: '0.3s'}}></div>
            </div>
            <span className="font-code-sm text-code-sm text-on-surface-variant italic">Agent is processing...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </section>

      <footer className="p-margin bg-background relative border-t border-outline-variant/20">
        <div className="max-w-5xl mx-auto relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-primary/20 to-transparent rounded-xl blur opacity-0 group-focus-within:opacity-100 transition duration-500"></div>
          
          <div className="relative flex items-end gap-sm bg-surface-container-low border border-outline-variant rounded-xl p-3 focus-within:border-primary/50 transition-all shadow-xl">
            <button className="p-2 text-on-surface-variant hover:text-primary transition-colors">
              <span className="material-symbols-outlined">add_circle</span>
            </button>
            <textarea 
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              className="flex-1 bg-transparent border-none focus:ring-0 resize-none py-2 font-body-md text-body-md text-on-surface placeholder:text-on-surface-variant/40 max-h-48 outline-none" 
              placeholder="Type a command or ask a question..." 
              rows={1}
            />
            <div className="flex items-center gap-sm">
              <button className="p-2 text-on-surface-variant hover:text-primary transition-colors hidden sm:block">
                <span className="material-symbols-outlined">mic</span>
              </button>
              <button 
                onClick={handleSubmit}
                disabled={!input.trim() || loading}
                className="bg-primary-container text-white p-2.5 rounded-lg hover:opacity-90 active:scale-95 transition-all flex items-center justify-center disabled:opacity-50"
              >
                <span className="material-symbols-outlined fill" style={{fontVariationSettings: "'FILL' 1"}}>send</span>
              </button>
            </div>
          </div>
        </div>
        <div className="text-center mt-md">
          <p className="font-body-sm text-[10px] text-on-surface-variant/30 uppercase tracking-widest font-medium">HJAI Neural Engine • Secure End-to-End Tunnel Active</p>
        </div>
      </footer>
    </div>
  );
}
