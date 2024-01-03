module.exports = {
    apps: [{
        name: "HexBug",
        script: "./scripts/pm2/run.sh",
        min_uptime: "15s",
        max_restarts: 3,
    }]
}
