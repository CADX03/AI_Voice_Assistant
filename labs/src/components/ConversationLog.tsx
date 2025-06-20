import { ProcessedMessage } from '../utils/WebSocketMsgProtocol.ts';
import './LabsPage.css';
import './ConversationLog.css';
import { useEffect, useRef, useState } from 'react';
import Icon from './Icon.tsx';
import * as Constants from '../constants/index.ts';
interface MessageWithTimestamp extends ProcessedMessage {
  timestamp?: string | number;
}

interface ConversationLogProps {
  messages: MessageWithTimestamp[];
}

function ConversationLog({ messages }: ConversationLogProps) {

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true)
  
  // handle download output json
  const handleDownload = (jsonString: string) => {
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'conversation_output.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Scroll to the bottom when messages change
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  // Detect user scrolling to disable auto-scrolling
  useEffect(() => {
    const handleScroll = () => {
      if (!chatContainerRef.current) return;

      // Calculate how far the user is from the bottom
      const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100; // Within 100px of bottom

      // Disable auto-scroll if user scrolls up significantly
      setAutoScroll(isNearBottom);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  
  return (
    <div className="chat-container">
      <div className="chat-timeline">
        {messages.map((msg, idx) => {
          // Determine sender and alignment based on message type
          let sender = '';
          let align = '';
          if (msg.type === 'text_stt' || msg.type === 'timestamp_stt') {
            sender = 'You';
            align = 'left';
          } else if (msg.type === 'text_tts' || msg.type === 'timestamp_tts' || msg.type === 'timestamp_llm') {
            sender = 'Bot';
            align = 'right';
          } else if (msg.type === 'text_output') {
            sender = 'Output';
            align = 'center';
          }
          return (
            <div key={idx} className={`chat-message-row ${align}`}>
              <div className={`chat-bubble ${align}`}>
                <div className="chat-label">
                  {sender}
                  <span className="chat-timestamp" style={{ color: '#111' }}>
                    {(() => {
                      // If timestamp exists, use it
                      if (msg.timestamp) {
                        return new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                      }
                      // Otherwise, generate a unique fallback using current time minus idx * 1000ms
                      const fallbackTime = new Date(Date.now() - (messages.length - idx - 1) * 1000);
                      return fallbackTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                    })()}
                  </span>
                </div>
                <div className="output-text">
                  {msg.type === 'text_output' ? (
                    <div className="output-bg">
                      <div className="output_container">
                        {(() => {
                          try {
                            let raw = msg.value.replace('Output: ', '').trim();
                            if (raw.endsWith('`')) raw = raw.slice(0, -1).trim();
                            const json = JSON.parse(raw);
                            console.log('Parsed JSON:', json);
                            return (
                              <div className="output-friendly">
                                {json.identificacao_cliente && (
                                  <>
                                    <div><strong>Número de Encomenda:</strong> {json.identificacao_cliente.numero_encomenda ?? 'N/A'}</div>
                                    <div><strong>Email:</strong> {json.identificacao_cliente.email ?? 'N/A'}</div>
                                  </>
                                )}
                                {json.tipificacao && (
                                  <div style={{ marginTop: '12px' }}>
                                    <strong>Tipificação:</strong> {json.tipificacao}
                                  </div>
                                )}
                                {'redirecionamento' in json && (
                                  <div style={{ marginTop: '12px' }}>
                                    <strong>Redirecionamento:</strong> {json.redirecionamento ? 'Sim' : 'Não'}
                                  </div>
                                )}
                                {json.resumo && (
                                  <div style={{marginTop: '12px'}}><strong>Resumo:</strong> {json.resumo}</div>
                                )}
                              </div>
                            );
                          } catch (e) {
                            return <pre className="pretty-json">{msg.value.replace('Output: ', '')}</pre>;
                          }
                        })()}
                      </div>
                      <div className="download_container">
                          <div className="download_button" onClick={() => handleDownload(msg.value.replace('Output: ', ''))}>
                              <span>DOWNLOAD JSON</span>
                              <Icon 
                                  className="download_icon"
                                  altName="Go-to arrow" 
                                  icon={Constants.icons.download} 
                                  size={1} />
                          </div>
                      </div>
                      <div className="end_message pulse">
                        Thanks for trying the demo! We value your voice — click the Feedback button at the bottom left!
                      </div>
                    </div>
                  ) : (
                    <span>{msg.value.replace(/^(STT: |TTS: )/, '')}</span>
                  )}
                </div>
              </div>
              {/* Timeline vertical line */}
              {idx < messages.length - 1 && <div className="chat-timeline-line" />}
            </div>
          );
        })}
        {/* Scroll to the bottom div */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

export default ConversationLog;