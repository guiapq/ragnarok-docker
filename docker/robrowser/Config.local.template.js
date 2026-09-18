window.ROConfigLocal = {

    socketProxy: "ws://${RO_IP}:5999",
    remoteClient: "${RO_REMOTE_CLIENT}",

    servers: [{
        display: "Docker Ragnarok",
        desc: "rAthena Docker Server",

        address: "${RO_IP}",
        port: ${RO_PORT},

        version: ${RO_VERSION},
        langtype: ${RO_LANGTYPE},

        packetver: ${RO_PACKETVER},
        renewal: true,

        packetKeys: ${RO_PACKETKEYS}
    }],

    loadLua: true,
    customItemInfo: [
        "data/System/itemInfo.lua"
    ],

    skipServerList: false,
    skipIntro: false
};
