async function loadUsers() {
    const res = await fetch('/api/admin/users', { headers: {'Authorization': `Bearer ${localStorage.token}`}});
    const users = await res.json();
    const tbody = document.querySelector('tbody');
    
    tbody.innerHTML = users.map(user => `
        <tr class="${user.status === 'pending' ? 'bg-indigo-900/10' : ''}">
            <td class="p-4">${user.username}</td>
            <td class="p-4">${user.role}</td>
            <td class="p-4">${user.status}</td>
            <td class="p-4">
                ${user.status === 'pending' ? 
                    `<button onclick="approve('${user._id}')" class="text-emerald-400">Approve</button>` : 
                    'Active'}
            </td>
        </tr>
    `).join('');
}

async function approve(id) {
    await fetch(`/api/admin/approve/${id}`, { method: 'POST', headers: {'Authorization': `Bearer ${localStorage.token}`}});
    loadUsers(); // Refresh the list
}
loadUsers();