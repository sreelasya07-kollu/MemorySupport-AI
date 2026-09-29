import React, { useEffect, useState } from "react";
import { api } from "./api";
import {
  LayoutDashboard, MessageSquare, Users, Brain, Ticket, LogOut,
  ShieldCheck, ChevronRight, AlertTriangle, CheckCircle2, XCircle,
  Send, Sparkles, Settings, RefreshCw, UserRound, Clock
} from "lucide-react";

function Login({ onLogin }) {
  const [register, setRegister] = useState(false);
  const [form, setForm] = useState({name:"", email:"sarah@example.com", password:"Sarah123!"});
  const [error, setError] = useState("");
  const [loading,setLoading]=useState(false);

  async function submit(e) {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const data = await api(register ? "/api/auth/register" : "/api/auth/login", {
        method:"POST", body:JSON.stringify(form)
      });
      localStorage.setItem("token",data.access_token);
      localStorage.setItem("user",JSON.stringify(data.user));
      onLogin(data.user);
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return <div className="auth"><div className="auth-card">
    <div className="brand large"><Brain size={30}/> MemorySupport AI</div>
    <p className="muted">Customer support that remembers what worked.</p>
    <form onSubmit={submit}>
      {register && <input placeholder="Full name" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} required/>}
      <input type="email" placeholder="Email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} required/>
      <input type="password" placeholder="Password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} required/>
      {error && <div className="error">{error}</div>}
      <button className="primary full" disabled={loading}>{loading?"Signing in…":register?"Create customer account":"Sign in"}</button>
    </form>
    <button className="link" onClick={()=>setRegister(!register)}>{register?"Already have an account? Sign in":"Create a customer account"}</button>
    <div className="demo-box"><b>Demo accounts</b><br/>Customer: sarah@example.com / Sarah123!<br/>Support: alex@example.com / Alex123!<br/>Admin: admin@example.com / Admin123!</div>
  </div></div>
}

function Shell({user,setUser,children,page,setPage}) {
  const customer=user.role==="CUSTOMER";
  const items=customer
    ? [["dashboard","Dashboard",LayoutDashboard],["chat","Support Chat",MessageSquare],["tickets","My Tickets",Ticket],["memory","My Memory",Brain]]
    : [["dashboard","Dashboard",LayoutDashboard],["customers","Customers",Users],["tickets","Tickets",Ticket],["memory","Memory",Brain],["escalations","Escalations",AlertTriangle],["recurring","Recurring Issues",RefreshCw],...(user.role==="ADMIN"?[["settings","Settings",Settings]]:[])];
  function logout(){localStorage.clear();setUser(null)}
  return <div className="app"><aside>
    <div className="brand"><Brain/> MemorySupport</div><div className="role">{user.role.replace("_"," ")}</div>
    <nav>{items.map(([id,label,Icon])=><button className={page===id?"active":""} onClick={()=>setPage(id)} key={id}><Icon size={18}/><span>{label}</span></button>)}</nav>
    <div className="side-bottom"><div className="user-mini"><div className="avatar">{user.name[0]}</div><div><b>{user.name}</b><span>{user.email}</span></div></div><button onClick={logout}><LogOut size={17}/> Logout</button></div>
  </aside><main>
    <header><div><span className="eyebrow">AI CUSTOMER SUPPORT</span><h1>{pageTitle(page)}</h1></div><MemoryStatus/></header>
    <div className="content">{children}</div>
  </main></div>
}
function pageTitle(page){return ({dashboard:"Dashboard",chat:"Support Chat",tickets:"Tickets",memory:"Memory",customers:"Customers",escalations:"Escalations",recurring:"Recurring Issues",settings:"Settings"})[page]||"Dashboard"}

function MemoryStatus(){
  const [s,setS]=useState(null);
  useEffect(()=>{api("/api/memory/status").then(setS).catch(()=>{})},[]);
  return <div className="status"><span className={s?.enabled?"":"offline"}/>{s?.enabled?"Hindsight connected":"Local memory fallback"}</div>
}

function Dashboard({user,setPage}){
  const [data,setData]=useState(null);
  useEffect(()=>{api(user.role==="CUSTOMER"?"/api/tickets":"/api/admin/dashboard").then(setData).catch(()=>{})},[]);
  if(user.role==="CUSTOMER"){
    const tickets=data||[];
    return <><div className="hero"><div><div className="tag">MEMORY-POWERED SUPPORT</div><h2>Welcome back, {user.name.split(" ")[0]}.</h2><p>Your support agent remembers previous issues and solutions so you don't have to start over.</p><button className="primary" onClick={()=>setPage("chat")}><MessageSquare size={17}/> Ask Support</button></div><div className="hero-icon"><Brain size={80}/></div></div>
    <div className="stats"><Stat label="Open tickets" value={tickets.filter(t=>["Open","In Progress","Escalated"].includes(t.status)).length}/><Stat label="Resolved" value={tickets.filter(t=>t.status==="Resolved").length}/><Stat label="Total tickets" value={tickets.length}/></div>
    <div className="section"><h3>What makes MemorySupport different?</h3><div className="feature-grid"><Feature title="Remembers" text="Previous problems and customer context."/><Feature title="Learns" text="Successful and failed solutions are remembered."/><Feature title="Personalizes" text="Future support uses customer history."/><Feature title="Escalates" text="Repeated failures can reach a human." /></div></div></>
  }
  return <><div className="stats"><Stat label="Customers" value={data?.customers??"—"}/><Stat label="Tickets" value={data?.tickets??"—"}/><Stat label="Resolved" value={data?.resolved??"—"}/><Stat label="Escalated" value={data?.escalated??"—"}/><Stat label="Memories" value={data?.memories??"—"}/></div>
  <div className="section"><h3>Hindsight status</h3><p className="muted">{data?.hindsight?.message||"Checking…"}</p></div>
  {data?.recurring_issues?.length>0&&<div className="section"><h3>Top recurring issues</h3>{data.recurring_issues.map(x=><div className="mini-ticket" key={x.issue}><b>{x.issue}</b><span>{x.count} cases · {x.affected_customers} customers</span><span className="pill">{x.severity}</span></div>)}</div>}
  </>}

function Stat({label,value}){return <div className="stat"><span>{label}</span><strong>{value}</strong></div>}
function Feature({title,text}){return <div className="feature"><div className="feature-icon"><Brain size={18}/></div><div><b>{title}</b><p>{text}</p></div></div>}

function Chat(){
  const [messages,setMessages]=useState([]),[text,setText]=useState(""),[ticketId,setTicketId]=useState(null),[last,setLast]=useState(null),[sending,setSending]=useState(false),[feedbackDone,setFeedbackDone]=useState(false);
  async function send(){if(!text.trim()||sending)return;const current=text;setText("");setMessages(m=>[...m,{role:"you",text:current}]);setSending(true);setFeedbackDone(false);try{const r=await api("/api/chat",{method:"POST",body:JSON.stringify({message:current,ticket_id:ticketId})});setTicketId(r.ticket_id);setMessages(m=>[...m,{role:"agent",text:r.response}]);setLast(r)}catch(e){setMessages(m=>[...m,{role:"agent",text:"Sorry: "+e.message}])}finally{setSending(false)}}
  async function feedback(outcome){if(!last?.ticket_id)return;try{await api("/api/tickets/feedback",{method:"POST",body:JSON.stringify({ticket_id:last.ticket_id,outcome,solution:last.response})});setFeedbackDone(true);setMessages(m=>[...m,{role:"system",text:`Feedback saved: ${outcome}. Memory updated.`}]);}catch(e){setMessages(m=>[...m,{role:"system",text:e.message}])}}
  async function escalate(){if(!last?.ticket_id)return;try{const r=await api("/api/tickets/escalate",{method:"POST",body:JSON.stringify({ticket_id:last.ticket_id,reason:"Customer requested human help after unsuccessful troubleshooting."})});setMessages(m=>[...m,{role:"system",text:`Escalated successfully. Case ESC-${r.id}. A human support agent can now review the case.`}]);}catch(e){setMessages(m=>[...m,{role:"system",text:e.message}])}}
  return <div className="chat-layout"><div className="chat-panel">
    <div className="chat-top"><div><b>AI Support Agent</b><span>Persistent memory + Hindsight grounding</span></div><Sparkles/></div>
    <div className="messages">{messages.length===0&&<div className="empty-chat"><Brain size={40}/><h3>How can I help?</h3><p>Try: “My PDF upload crashes after the latest update.”</p></div>}{messages.map((m,i)=><div className={`msg ${m.role}`} key={i}><div className="bubble">{m.text}</div></div>)}{sending&&<div className="msg agent"><div className="bubble">Checking customer memory…</div></div>}</div>
    <div className="composer"><input value={text} onChange={e=>setText(e.target.value)} onKeyDown={e=>e.key==="Enter"&&send()} placeholder="Describe your issue..."/><button className="primary" onClick={send} disabled={sending}><Send size={17}/></button></div>
  </div><div className="insights"><h3>Agent context</h3>
    {!last?<div className="muted-box">Relevant customer memory, similar cases and reasoning will appear here.</div>:<>
      <div className="memory-card"><div className="card-title"><Brain size={16}/> {last.memory_source==="Hindsight"?"Hindsight memory recalled":"Customer memory"}</div>{last.memories?.length?last.memories.map((m,i)=><p key={i}>{m}</p>):<p className="muted">No strong memory match found.</p>}</div>
      <div className="memory-card"><div className="card-title"><ShieldCheck size={16}/> Why this response?</div>{last.recommendation_reasons?.map((r,i)=><p key={i}>✓ {r}</p>)}</div>
      {last.similar_cases?.length>0&&<div className="memory-card"><div className="card-title"><Ticket size={16}/> Similar cases</div>{last.similar_cases.map(c=><p key={c.id}><b>TKT-{String(c.id).padStart(5,"0")}</b> · {c.subject}<br/><span className="muted">{c.solution}</span></p>)}</div>}
      {last.failed_attempts>0&&<div className="memory-card"><div className="card-title"><AlertTriangle size={16}/> Attempts</div><p>{last.failed_attempts} previous solution outcome(s) recorded for this ticket.</p></div>}
      <div className="feedback"><b>Did this solution work?</b><div><button disabled={feedbackDone} onClick={()=>feedback("Worked")} className="success"><CheckCircle2 size={16}/> Worked</button><button disabled={feedbackDone} onClick={()=>feedback("Didn't Work")} className="danger"><XCircle size={16}/> Didn't Work</button></div>
      {last.escalation_suggested&&<button className="escalate" onClick={escalate}><AlertTriangle size={16}/> Escalate to Human</button>}
      {feedbackDone&&<button className="escalate" onClick={escalate}><AlertTriangle size={16}/> Need a human?</button>}
      </div>
    </>}</div></div>
}

function Tickets({user}){const [tickets,setTickets]=useState([]);useEffect(()=>{api("/api/tickets").then(setTickets).catch(()=>{})},[]);return <div className="section"><div className="section-head"><h3>{user.role==="CUSTOMER"?"My tickets":"All tickets"}</h3></div><div className="table"><div className="tr th"><span>ID</span><span>Subject</span><span>Priority</span><span>Status</span></div>{tickets.map(t=><div className="tr" key={t.id}><span>TKT-{String(t.id).padStart(5,"0")}</span><span>{t.subject}</span><span>{t.priority}</span><span className={`pill ${t.status.toLowerCase().replaceAll(" ","-")}`}>{t.status}</span></div>)}</div></div>}

function Customers({setPage,setSelected}){const [rows,setRows]=useState([]);useEffect(()=>{api("/api/customers").then(setRows).catch(()=>{})},[]);return <div className="section"><h3>Customers</h3><div className="table"><div className="tr th"><span>Name</span><span>Email</span><span>Action</span></div>{rows.map(c=><div className="tr" key={c.id}><span><b>{c.name}</b></span><span>{c.email}</span><span><button className="small" onClick={()=>{setSelected(c.id);setPage("customer-profile")}}>View profile <ChevronRight size={14}/></button></span></div>)}</div></div>}

function Memory({user,agentCustomerId}){
  const id=agentCustomerId||user.id; const [data,setData]=useState(null),[summary,setSummary]=useState(null);
  useEffect(()=>{api(`/api/customers/${id}`).then(setData).catch(()=>{});api(`/api/memory/customer/${id}/summary`).then(setSummary).catch(()=>{})},[id]);
  if(!data)return <div className="loading">Loading memory…</div>;
  return <div className="memory-page"><div className="profile-card"><div className="avatar big">{data.customer.name[0]}</div><div><h2>{data.customer.name}</h2><p>{data.customer.email}</p><span className="pill">{data.hindsight_source} Memory</span></div></div>
    {summary&&<div className="stats"><Stat label="Memories" value={summary.total_memories}/><Stat label="Successful" value={summary.successful_solutions}/><Stat label="Failed" value={summary.failed_solutions}/><Stat label="Tickets" value={summary.tickets}/><Stat label="Escalations" value={summary.escalations}/></div>}
    <div className="memory-columns"><div className="section"><h3>Memory Timeline</h3>{data.memories.map(m=><div className="timeline" key={m.id}><div className="dot"/><div><b>{m.kind.replaceAll("_"," ")}</b><p>{m.content}</p><small>{new Date(m.created_at).toLocaleString()}</small></div></div>)}{data.hindsight?.length>0&&<><h3>Hindsight memories</h3>{data.hindsight.map((m,i)=><div className="memory-card" key={i}><span className="pill">Hindsight</span><p>{m}</p></div>)}</>}</div>
    <div className="section"><h3>Tickets</h3>{data.tickets.map(t=><div className="mini-ticket" key={t.id}><b>TKT-{String(t.id).padStart(5,"0")}</b><span>{t.subject}</span><span className="pill">{t.status}</span></div>)}<h3 style={{marginTop:20}}>Escalations</h3>{data.escalations.map(x=><div className="mini-ticket" key={x.id}><b>ESC-{x.id}</b><span>{x.reason}</span><span className="pill">{x.status}</span></div>)}</div></div></div>
}

function CustomerProfile({customerId,setPage}){return <div><button className="small" onClick={()=>setPage("customers")}>← Back to customers</button><div style={{marginTop:15}}><Memory agentCustomerId={customerId}/></div></div>}

function Escalations(){const [rows,setRows]=useState([]);useEffect(()=>{api("/api/admin/escalations").then(setRows).catch(()=>{})},[]);return <div className="section"><h3>Escalations</h3>{rows.length===0?<div className="muted-box">No escalations yet.</div>:rows.map(x=><div className="escalation" key={x.id}><div><b>ESC-{x.id} · TKT-{String(x.ticket_id).padStart(5,"0")}</b><span>{x.reason}</span></div><pre>{x.summary}</pre></div>)}</div>}

function Recurring(){const [rows,setRows]=useState([]);useEffect(()=>{api("/api/admin/recurring-issues").then(setRows).catch(()=>{})},[]);return <div className="section"><h3>Recurring Customer Issues</h3><p className="muted">Patterns detected across support tickets.</p>{rows.length===0?<div className="muted-box">Not enough repeated ticket categories yet.</div>:rows.map(x=><div className="recurring" key={x.issue}><div><b>{x.issue}</b><span>{x.count} cases · {x.affected_customers} customers</span></div><div><span className="pill">{x.severity}</span><span className="muted">{x.open_tickets} open · {x.resolved_tickets} resolved</span></div></div>)}</div>}

function SettingsPage(){const [data,setData]=useState(null);useEffect(()=>{api("/api/admin/settings").then(setData).catch(()=>{})},[]);return <div className="section"><h3>System Settings</h3>{data?<><div className="setting-row"><b>Hindsight</b><span className="pill">{data.hindsight?.enabled?"Connected":"Local fallback"}</span></div><div className="setting-row"><b>AI provider</b><span className="pill">{data.ai_configured?"Configured":"Deterministic fallback"}</span></div><div className="setting-row"><b>Database</b><span className="pill resolved">{data.database}</span></div><div className="setting-row"><b>Version</b><span>{data.version}</span></div></>:<div className="loading">Loading…</div>}</div>}

export default function App(){
  const [user,setUser]=useState(()=>JSON.parse(localStorage.getItem("user")||"null"));
  const [page,setPage]=useState("dashboard"),[selected,setSelected]=useState(null);
  if(!user)return <Login onLogin={setUser}/>;
  let content;
  if(page==="dashboard")content=<Dashboard user={user} setPage={setPage}/>;
  else if(page==="chat")content=<Chat/>;
  else if(page==="tickets")content=<Tickets user={user}/>;
  else if(page==="memory")content=<Memory user={user}/>;
  else if(page==="customers")content=<Customers setPage={setPage} setSelected={setSelected}/>;
  else if(page==="customer-profile")content=<CustomerProfile customerId={selected} setPage={setPage}/>;
  else if(page==="escalations")content=<Escalations/>;
  else if(page==="recurring")content=<Recurring/>;
  else if(page==="settings")content=<SettingsPage/>;
  return <Shell user={user} setUser={setUser} page={page} setPage={setPage}>{content}</Shell>;
}
