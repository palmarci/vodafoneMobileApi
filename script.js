window.onload = function() {
	function getTimeDifference(unixTimestamp) {
		const currentTime = Math.floor(Date.now() / 1000);
		const timeDifference = unixTimestamp - currentTime;
		const absDifference = Math.abs(timeDifference);
		if (absDifference < 300) {
			return 'just now';
		} else if (absDifference < 3600) {
			const minutes = Math.floor(absDifference / 60);
			return `${minutes} minute${minutes > 1 ? 's' : ''}`;
		} else if (absDifference < 86400) {
			const hours = Math.floor(absDifference / 3600);
			const minutes = Math.floor((absDifference % 3600) / 60);
			return `${hours} hour${hours > 1 ? 's' : ''} ${minutes} minute${minutes > 1 ? 's' : ''}`;
		} else {
			const days = Math.floor(absDifference / 86400);
			const hours = Math.floor((absDifference % 86400) / 3600);
			return `${days} day${days > 1 ? 's' : ''} ${hours} hour${hours > 1 ? 's' : ''}`;
		}
	}
	var currentTimestamp = parseInt(document.getElementById("updated").innerText);
	var renewAtTimestamp = parseInt(document.getElementById("renew").innerText);
	document.getElementById("updated").innerHTML = getTimeDifference(currentTimestamp) + " ago";
	document.getElementById("renew").innerHTML = "in " + getTimeDifference(renewAtTimestamp);
};
