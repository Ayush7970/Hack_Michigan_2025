// Simplified negotiation services for compact pipeline

export const sendNegotiationMessage = async (
    message: string,
    agentProfile: any,
    conversationId: string = 'default'
) => {
    console.log("🔥 NEGOTIATION: Sending message");
    console.log("📨 Message:", message);
    console.log("🤖 Agent:", agentProfile?.name);

    try {
        const response = await fetch('http://localhost:8001/negotiate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                agent_profile: agentProfile,
                conversation_id: conversationId
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("📄 Response:", data);
        return data;
    } catch (err) {
        console.error("💥 Error sending message:", err);
        return null;
    }
};

export const getConversation = async (conversationId: string = 'default') => {
    try {
        const response = await fetch(`http://localhost:8001/conversation/${conversationId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (err) {
        console.error("💥 Error getting conversation:", err);
        return null;
    }
};

// Legacy support - keeping old function name
export const sendInput = sendNegotiationMessage;

