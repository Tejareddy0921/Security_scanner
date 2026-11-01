import '../style/pages/profile.css'

export default function Profile({ user }) {
  const initials = user?.name?.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase() || 'U'

  return (
    <div className="profile-page"><header className="page-heading"><span className="eyebrow">ACCOUNT DETAILS</span><h1>Your profile<span className="heading-dot">.</span></h1><p>A few details about yourSecurity_scanner account.</p></header><section className="profile-card"><div className="profile-banner"><span className="profile-avatar">{initials}</span><div><span className="eyebrow">SCAMGUARD MEMBER</span><h2>{user?.name}</h2></div><span className="profile-badge"><span /> Active</span></div><div className="profile-details"><div className="detail-row"><span>Full name</span><strong>{user?.name}</strong></div><div className="detail-row"><span>Email address</span><strong>{user?.email}</strong></div><div className="detail-row"><span>Account type</span><strong>Personal account</strong></div></div><p className="profile-note">Your profile and scan history are linked to yourSecurity_scanner account.</p></section></div>
  )
}
