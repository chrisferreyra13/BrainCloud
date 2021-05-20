import React, { Component } from 'react'
import {
	CCard,
	CCardBody,
	CCardGroup,
} from '@coreui/react'

import {connect} from 'react-redux'
import ChartChannel from './ChartChannel'
import ChartChannels from './ChartChannels'
import {SamplesToTimes} from '../../tools/Signal'


//import  CanvasJSReact from '../../canvasjs/canvasjs.react'
//import {Line} from 'react-chartjs-2'

class ChartTemporal extends Component {
    constructor(props){
        super(props);
		const nodePlot=this.props.elements.find((elem) => elem.id==this.props.nodeId) //Busco nodoPlot para setear los params
		let params={}
		if(nodePlot.params.channels==null){ 
			params={ //Default params
				channels:['EEG 016','EEG 017'], //Para ChartTemporal, los canales son una lista de strings
				minTimeWindow:null,
				maxTimeWindow:null,
				largeSize:'on',
				mediumSize:'off',
				smallSize:'off',
				
			}
		}else{
			params={
				channels:nodePlot.params.channels.split(','), // En params se guarda como ch separado por comas
				...nodePlot.params
			}
				
		}
		//const nodeTimeSeries=this.props.elements.find(n=> n.elementType=='TIME_SERIES')

		let data=[]
		let limit = this.props.data.data[0].length;
		let dataPoints = [];
		let minTimeIndex=0;
		let maxTimeIndex=limit;
		if(params.minTimeWindow!=null){
			minTimeIndex=Math.round(params.minTimeWindow*this.props.data.sFreq)
			if(minTimeIndex>=limit) minTimeIndex=0; //Se paso, tira error
		}
		if(params.maxTimeWindow!=null){
			maxTimeIndex=Math.round(params.maxTimeWindow*this.props.data.sFreq)
			if(maxTimeIndex>limit) maxTimeIndex=limit; //Se paso, tira error
		}

		if(params.channels.length!=0){
			// Si no coinciden hay error, tenerlo en cuenta para hacer una excepcion
			const idxs=params.channels.map((ch) => this.props.data.chNames.findIndex((chName) => ch===chName))
			for(var j = 0; j < params.channels.length; j += 1){
				for (var i = minTimeIndex; i < maxTimeIndex; i += 1) {
					dataPoints.push({
					x: SamplesToTimes(i,this.props.data.sFreq,3),
					y: Math.pow(10,6)*this.props.data.data[idxs[j]][i]
				});
				}
				data.push(dataPoints)
				dataPoints=[]
			}
		}else{
			for (var i = minTimeIndex; i < maxTimeIndex; i += 1) {
				dataPoints.push({
				x: SamplesToTimes(i,this.props.data.sFreq,3),
				y: Math.pow(10,6)*this.props.data.data[1][i]
			});
			}
			data=dataPoints
		}	
		let style={} //Seteando las dimensiones del grafico en base a los parametros
		//Cambiar esto, no va a funcionar, el form solo envia uno de los 3, los otros 2 quedan undefined
		if(params.largeSize==='on'){// TODO: Mejorar esto, no funciona el dividir de forma inteligente
			style={
				height:'75vh',
			}
		}else if(params.mediumSize==='on'){
			style={
				height:'60vh',
				width:'600px'
			}
		}else{
			style={
				height:'40vh',
				width:'600px'
			}
		}

		this.state={
			nodeId:this.props.nodeId,
			params:params,
			style:style,
			data:data

		}

    }

    render() {
		const nodeTimeSeries=this.props.elements.find(n=> n.elementType=='TIME_SERIES')
		if(this.props.data.data[1]==undefined){
			return null
		}else{
			return (
				<div>
					<CCard style={this.state.style}>
						<CCardBody>
							{this.state.params.channels.length<=1 ?
							<ChartChannel
							data={this.state.data}
							chartStyle={{height: '100%', width:'100%'}}
							channel={this.state.params.channels[1]==undefined ? this.props.data.chNames[1] : this.state.params.channels[1]}
							/> :
							<ChartChannels 
							data={this.state.data}
							chartStyle={{height: '100%', width:'100%'}}
							channels={this.state.params.channels}
							/>
						}
						</CCardBody>
					</CCard>
				</div>
			)	
		}
    }
}
const mapStateToProps = (state) => {
	return{
	  fileInfo: state.file.fileInfo,
	  elements:state.diagram.elements,
	};
  }
  
  const mapDispatchToProps = (dispatch) => {
	return {
		//
	};
  };
export default connect(mapStateToProps, mapDispatchToProps)(ChartTemporal)