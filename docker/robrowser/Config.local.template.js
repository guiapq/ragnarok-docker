window.ROConfigLocal = {

    // Proxy WebSocket dinâmico baseado no host onde o navegador abriu o roBrowser
    socketProxy: (location.protocol === "https:" ? "wss://" : "ws://") + location.hostname + ":5999",
    remoteClient: "${RO_REMOTE_CLIENT}",

    servers: [{
        display: "Docker Ragnarok",
        desc: "rAthena Docker Server",

        // Endereço interno que o wsProxy (dentro do container robrowser) usa para conectar ao rAthena
        address: "ragnarok-server",
        port: ${RO_PORT},

        version: ${RO_VERSION},
        langtype: ${RO_LANGTYPE},

        packetver: ${RO_PACKETVER},
        renewal: false,

        packetKeys: ${RO_PACKETKEYS}
    }],

    forceUseAddress: true,
    disableKorean: true,
    enableConsole: true,
    skipServerList: false,
    skipIntro: false,

    // Enable Lua engine for rich, modern itemInfo and skilldescript
    // Usando apenas .lua textual — evita dependência do .lub binário do bRO
    loadLua: true,
    customItemInfo: ['System/itemInfo.lua']
};

